from __future__ import annotations

import collections
import pathlib
import typing
from enum import Enum

from src import util
from src.logic import mtl as m


class Trace:
    def __init__(
        self,
        trace: list[dict[str, bool | int]],
        loop_start: int | None = None,
    ) -> None:
        # NuXmv identifies loops by duplicating the state
        # at the start of the loop at the end of the trace
        if loop_start is None:
            self.loop_start = self.periodic_trace_idx(trace)
            self.trace = trace[:-1]
        else:
            self.loop_start = loop_start
            self.trace = trace

    def to_markings(self) -> dict[m.Mtl, list[bool]]:
        markings: dict[m.Mtl, list[bool]] = {}
        for state in self.trace:
            for k, v in state.items():
                f = m.Prop(k)
                if f not in markings:
                    markings[f] = []
                assert type(v) is bool
                markings[f].append(v)
        return markings

    def periodic_trace_idx(self, trace: list[dict[str, bool | int]]) -> int:
        if len(trace) > 0:
            last = trace[-1]
            for i in range(len(trace) - 2, -1, -1):
                if last == trace[i]:
                    return i
        msg = "Cannot identify loop in trace"
        raise RuntimeError(msg)

    def idx(self, i: int) -> int:
        if i >= len(self.trace):
            j = (i - self.loop_start) % (len(self.trace) - self.loop_start)
            return j + self.loop_start
        return i

    def right_idx(self, a: int) -> int:
        """Get the index of the right side of the trace."""
        if a < self.loop_start:
            return len(self.trace) - 1
        suf_len = len(self.trace) - self.loop_start
        return a + suf_len - 1

    def __len__(self) -> int:
        return len(self.trace)

    def __getitem__(self, i: int) -> dict[str, bool | int]:
        return self.trace[self.idx(i)]

    def __iter__(self) -> typing.Iterator[dict[str, bool | int]]:
        return iter(self.trace)


class Mutability(Enum):
    VARIABLE = 1
    CONSTANT = 2


def get_variable_types(
    trace: Trace,
) -> dict[str, tuple[Mutability, str]]:
    variable_values = collections.defaultdict(set)
    for state in trace:
        for k, v in state.items():
            variable_values[k].add(v)
    variable_types = {}
    for var, values in variable_values.items():
        if all(isinstance(v, bool) for v in values):
            variable_types[var] = (Mutability.VARIABLE, "boolean")
        elif all(isinstance(v, int) for v in values):
            max_val = max(values)
            min_val = min(values)
            if min_val == max_val:
                variable_types[var] = (Mutability.CONSTANT, f"{min_val}")
            else:
                variable_types[var] = (
                    Mutability.VARIABLE,
                    f"{min_val}..{max_val}",
                )
        else:
            msg = f"Mixed or unsupported types for variable '{var}': {values}"
            raise ValueError(
                msg,
            )
    return variable_types


def generate_vars(
    variable_types: dict[str, tuple[Mutability, str]],
    num_states: int,
) -> list[str]:
    lines = ["VAR"]
    lines.append(f"  state : 0..{num_states - 1};")
    for var, (mutability, smv_type) in variable_types.items():
        if mutability == Mutability.VARIABLE:
            lines.append(f"  {var} : {smv_type};")
    return lines


def generate_defines(
    variable_types: dict[str, tuple[Mutability, str]],
) -> list[str]:
    lines = []
    if any(
        mutability == Mutability.CONSTANT
        for _, (mutability, _) in variable_types.items()
    ):
        lines.append("DEFINE")
        for var, (mutability, smv_type) in variable_types.items():
            if mutability == Mutability.CONSTANT:
                lines.append(f"  {var} := {smv_type};")
    return lines


def generate_assignments(
    trace: Trace,
    variable_types: dict[str, tuple[Mutability, str]],
    num_states: int,
) -> list[str]:
    lines = ["ASSIGN"]
    lines.append("  init(state) := 0;")
    lines.append("  next(state) := case")
    for i in range(num_states):
        next_state = i + 1 if i < num_states - 1 else trace.loop_start
        lines.append(f"    state = {i} : {next_state};")
    lines.append("    TRUE : state;")
    lines.append("  esac;")
    variables = {
        var
        for var, (mutability, _) in variable_types.items()
        if mutability == Mutability.VARIABLE
    }
    for var in variables:
        val = trace[0][var]
        val_str = (
            "TRUE" if val is True else "FALSE" if val is False else str(val)
        )
        lines.append(f"  init({var}) := {val_str};")
        lines.append(f"  next({var}) := case")
        for i, state in enumerate(trace):
            im = (i - 1) % num_states
            val = state[var]
            val_str = (
                "TRUE" if val is True else "FALSE" if val is False else str(val)
            )
            lines.append(f"    state = {im} : {val_str};")
        lines.append(f"    TRUE : {val_str};")
        lines.append("  esac;")
    return lines


def generate_trace_smv(trace: Trace) -> str:
    num_states = len(trace)
    variable_types = get_variable_types(trace)
    lines = ["MODULE main"]
    lines += generate_vars(variable_types, num_states)
    lines += generate_defines(variable_types)
    lines += generate_assignments(trace, variable_types, num_states)
    return "\n".join(lines)


def write_trace_smv(
    filepath: pathlib.Path,
    trace: Trace,
    formula: m.Mtl,
) -> list[m.Mtl]:
    trace_smv = generate_trace_smv(trace)
    ltlspec_smv, subformulae = m.generate_subformulae_smv(formula, len(trace))
    with filepath.open("w", encoding="utf-8") as f:
        f.write(trace_smv + "\n\n" + ltlspec_smv + "\n")
    return subformulae


def parse_nuxmv_output(
    output: str,
    subformulae: list[m.Mtl],
    num_states: int,
) -> dict[m.Mtl, list[bool]]:
    lines = output.split("\n")
    lines = list(
        filter(
            lambda line: line.startswith("-- ")
            and not line.startswith(
                "-- as demonstrated by the following execution sequence",
            ),
            lines,
        ),
    )
    markings: dict[m.Mtl, list[bool]] = {}
    for i, f in enumerate(subformulae):
        markings[f] = []
        for j in range(num_states):
            idx = i * num_states + j
            if lines[idx].endswith("true"):
                markings[f].append(True)
            elif lines[idx].endswith("false"):
                markings[f].append(False)
            else:
                msg = f"line '{lines[idx]}' is malformed"
                raise ValueError(msg)
    return markings


class Marking:
    loop_str = "=Lasso="

    def __init__(self, trace: Trace, formula: m.Mtl) -> None:
        self.trace = trace
        self.loop_start = trace.loop_start
        self.markings = trace.to_markings()
        self[formula]

    def mark_trace_with_nusmv(
        self,
        trace: Trace,
        formula: m.Mtl,
    ) -> dict[m.Mtl, list[bool]]:
        subformulae = write_trace_smv(
            pathlib.Path("res/trace.smv"),
            trace,
            formula,
        )
        out = util.run_and_capture(["nuXmv", "-source", "res/check_trace.txt"])
        return parse_nuxmv_output(out, subformulae, len(trace))

    def add_loop_str(self, max_len: int) -> str:
        out = f"{self.loop_str:<{max_len}}  "
        for i in range(len(self.trace)):
            if i == self.loop_start and i == len(self.trace) - 1:
                out += "⊔"
            elif i == self.loop_start:
                out += "└─"
            elif i == len(self.trace) - 1:
                out += "┘"
            elif i > self.loop_start:
                out += "──"
            else:
                out += "  "
        return out

    def get(self, f: m.Mtl, i: int) -> bool:
        return self[f][self.trace.idx(i)]

    def __getitem__(self, f: m.Mtl) -> list[bool]:
        if f in self.markings:
            return self.markings[f]
        if isinstance(f, m.Prop):
            msg = f"Proposition '{f}' not found in markings. "
            raise TypeError(msg)
        if isinstance(f, m.Not):
            bs = [not v for v in self[f.operand]]
        elif isinstance(f, m.And):
            bs = [
                left and right
                for left, right in zip(self[f.left], self[f.right])
            ]
        elif isinstance(f, m.Or):
            bs = [
                left or right
                for left, right in zip(self[f.left], self[f.right])
            ]
        elif isinstance(f, m.Implies):
            bs = [
                (not left) or right
                for left, right in zip(self[f.left], self[f.right])
            ]
        elif isinstance(f, m.Eventually):
            vs = self[f.operand]
            bs = [False] * len(vs)
            for i in range(len(bs)):
                right_idx = (
                    f.interval[1] + 1 if f.interval[1] is not None else len(vs)
                )
                bs[i] = any(
                    vs[self.trace.idx(j)]
                    for j in range(i + f.interval[0], i + right_idx)
                )
        elif isinstance(f, m.Always):
            vs = self[f.operand]
            bs = [False] * len(vs)
            for i in range(len(bs)):
                right_idx = (
                    f.interval[1] + 1 if f.interval[1] is not None else len(vs)
                )
                bs[i] = all(
                    vs[self.trace.idx(j)]
                    for j in range(i + f.interval[0], i + right_idx)
                )
            self.markings[f] = bs
            return bs
        elif isinstance(f, m.Until):
            rights = self[f.right]
            lefts = self[f.left]
            bs = [False] * len(rights)
            for i in range(len(bs)):
                right_idx = (
                    f.interval[1] + 1
                    if f.interval[1] is not None
                    else len(rights) - i
                )
                for j in range(i + f.interval[0], i + right_idx):
                    k = self.trace.idx(j)
                    if rights[k]:
                        bs[i] = True
                        break
                    if not lefts[k]:
                        break
        elif isinstance(f, m.Release):
            rights = self[f.right]
            lefts = self[f.left]
            bs = [False] * len(rights)
            for i in range(len(bs)):
                right_idx = (
                    f.interval[1] + 1
                    if f.interval[1] is not None
                    else len(rights) - i
                )
                for j in range(i + f.interval[0], i + right_idx):
                    k = self.trace.idx(j)
                    if not rights[k]:
                        break
                    if lefts[k]:
                        bs[i] = True
                        break
        else:
            msg = f"Unsupported MTL construct: {f}"
            raise TypeError(msg)
        self.markings[f] = bs
        return bs

    def __str__(self) -> str:
        out = ""
        subformulae = list(self.markings.keys())
        max_len = max(
            len(self.loop_str),
            *(len(m.to_string(f)) for f in subformulae),
        )
        for f in reversed(subformulae):
            s = m.to_string(f)
            out += f"{s:<{max_len}} "
            for marking in self.markings[f]:
                if marking:
                    out += "│●"
                else:
                    out += "│ "
            out += "│\n"
        out += self.add_loop_str(max_len)
        return out
