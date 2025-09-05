from __future__ import annotations

import collections
import logging
import typing
from enum import Enum

from src.logic import mtl as m

logger = logging.getLogger(__name__)


def expand_nuxmv_trace(
    trace: list[dict[str, bool | int | str]],
) -> list[dict[str, bool | int | str]]:
    """
    NuXmv gives traces in a compact form, where if a variable does not change
    then its value is not included in the state. We expand the trace to
    include all variable assignments at each step.
    """
    variables = trace[0].keys()
    for i, state in enumerate(trace):
        for var in variables:
            if var not in state:
                state[var] = trace[i - 1][var]
    return trace


class Trace:
    def __init__(
        self,
        trace: list[dict[str, bool | int | str]],
        loop_start: int,
    ) -> None:
        trace = expand_nuxmv_trace(trace)
        assert loop_start < len(trace)
        self.loop_start = loop_start
        self.trace = trace

    def find_loop(self) -> bool:
        """
        Find a loop in the trace.
        Return True if a loop is found, False otherwise.
        """
        loop = self.periodic_trace_idx(self.trace)
        if loop is None:
            return False
        logger.info(
            "Trace of len %d has loop indices (%d, %d)",
            len(self.trace),
            loop[0],
            loop[1],
        )
        self.loop_start = loop[0]
        self.trace = self.trace[: loop[1]]
        return True

    def to_markings(self) -> dict[m.Mtl, list[bool | int]]:
        markings: dict[m.Mtl, list[bool | int]] = {}
        for state in self.trace:
            for k, v in state.items():
                if not isinstance(v, (bool, int)):
                    continue
                f = m.Prop(k)
                if f not in markings:
                    markings[f] = []
                markings[f].append(v)
        return markings

    def to_bool_markings(self) -> dict[m.Mtl, list[bool]]:
        markings: dict[m.Mtl, list[bool]] = {}
        for state in self.trace:
            for k, v in state.items():
                if not isinstance(v, bool):
                    continue
                f = m.Prop(k)
                if f not in markings:
                    markings[f] = []
                markings[f].append(v)
        return markings

    def periodic_trace_idx(
        self,
        trace: list[dict[str, bool | int | str]],
    ) -> tuple[int, int] | None:
        """
        Attempts to find the indices of a loop in the trace.
        If none is found, then None is returned.

        Loops are found by checking for repeated states,
        and we return the coincident indices as a tuple.
        """
        if not trace:
            return None
        for j, back in reversed(list(enumerate(trace))):
            for i in range(j - 1, -1, -1):
                if back == trace[i]:
                    return i, j
        logger.warning("Cannot identify loop in trace")
        return None

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

    def __getitem__(self, i: int) -> dict[str, bool | int | str]:
        return self.trace[self.idx(i)]

    def __iter__(self) -> typing.Iterator[dict[str, bool | int | str]]:
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


def parse_nuxmv_output(
    output: str,
    subformulae: list[m.Mtl],
    num_states: int,
) -> dict[m.Mtl, list[bool | int]]:
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
    markings: dict[m.Mtl, list[bool | int]] = {}
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
    def __init__(self, trace: Trace, formula: m.Mtl) -> None:
        self.trace = trace
        self.markings = trace.to_bool_markings()
        self[formula]  # pylint: disable=pointless-statement

    def get(self, f: m.Mtl, i: int) -> bool:
        return self[f][self.trace.idx(i)]

    def _get_and(self, left: m.Mtl, right: m.Mtl) -> list[bool]:
        return [l and r for l, r in zip(self[left], self[right])]  # noqa: E741

    def _get_or(self, left: m.Mtl, right: m.Mtl) -> list[bool]:
        return [l or r for l, r in zip(self[left], self[right])]  # noqa: E741

    def _get_implies(self, left: m.Mtl, right: m.Mtl) -> list[bool]:
        return [
            (not l) or r for l, r in zip(self[left], self[right])  # noqa: E741
        ]

    def _get_eventually(
        self,
        operand: m.Mtl,
        interval: m.Interval,
    ) -> list[bool]:
        vs = self[operand]
        bs = [False] * len(vs)
        for i in range(len(vs)):
            right_idx = interval[1] + 1 if interval[1] is not None else len(vs)
            bs[i] = any(
                vs[self.trace.idx(j)]
                for j in range(i + interval[0], i + right_idx)
            )
        return bs

    def _get_always(self, operand: m.Mtl, interval: m.Interval) -> list[bool]:
        vs = self[operand]
        bs = [False] * len(vs)
        for i in range(len(vs)):
            right_idx = interval[1] + 1 if interval[1] is not None else len(vs)
            bs[i] = all(
                vs[self.trace.idx(j)]
                for j in range(i + interval[0], i + right_idx)
            )
        return bs

    def _get_until(
        self,
        left: m.Mtl,
        right: m.Mtl,
        interval: m.Interval,
    ) -> list[bool]:
        rights = self[right]
        lefts = self[left]
        bs = [False] * len(rights)
        for i in range(len(rights)):
            right_idx = (
                interval[1] + 1 if interval[1] is not None else len(rights) - i
            )
            for j in range(i + interval[0], i + right_idx):
                k = self.trace.idx(j)
                if rights[k]:
                    bs[i] = True
                    break
                if not lefts[k]:
                    break
        return bs

    def _get_release(
        self,
        left: m.Mtl,
        right: m.Mtl,
        interval: m.Interval,
    ) -> list[bool]:
        rights = self[right]
        lefts = self[left]
        bs = [False] * len(rights)
        for i in range(len(rights)):
            right_idx = (
                interval[1] + 1 if interval[1] is not None else len(rights) - i
            )
            for j in range(i + interval[0], i + right_idx):
                k = self.trace.idx(j)
                if not rights[k]:
                    break
                if lefts[k]:
                    bs[i] = True
                    break
        return bs

    def _get_next(self, operand: m.Mtl) -> list[bool]:
        operands = self[operand]
        return [operands[self.trace.idx(i + 1)] for i in range(len(operands))]

    def __getitem__(self, f: m.Mtl) -> list[bool]:
        if f in self.markings:
            return self.markings[f]
        if isinstance(f, m.TrueBool):
            return [True] * len(self.trace)
        if isinstance(f, m.FalseBool):
            return [False] * len(self.trace)
        if isinstance(f, m.Prop):
            msg = f"Proposition '{f}' not found in markings. "
            raise TypeError(msg)
        if isinstance(f, m.Not):
            bs = [not v for v in self[f.operand]]
        elif isinstance(f, m.And):
            bs = self._get_and(f.left, f.right)
        elif isinstance(f, m.Or):
            bs = self._get_or(f.left, f.right)
        elif isinstance(f, m.Implies):
            bs = self._get_implies(f.left, f.right)
        elif isinstance(f, m.Eventually):
            bs = self._get_eventually(f.operand, f.interval)
        elif isinstance(f, m.Always):
            bs = self._get_always(f.operand, f.interval)
        elif isinstance(f, m.Until):
            bs = self._get_until(f.left, f.right, f.interval)
        elif isinstance(f, m.Release):
            bs = self._get_release(f.left, f.right, f.interval)
        elif isinstance(f, m.Next):
            bs = self._get_next(f.operand)
        else:
            msg = f"Unsupported MTL construct: {f}"
            raise TypeError(msg)
        self.markings[f] = bs
        return bs

    def __str__(self) -> str:
        return bool_markings_to_str(self.markings, self.trace.loop_start)


def _get_trace_indices_str(trace_len: int, max_len: int) -> str:
    out = ""
    if trace_len > 10:  # noqa: PLR2004
        out += " " + " " * max_len
        for i in range(trace_len):
            tens = i // 10
            out += f" {tens if tens > 0 else ' '}"
        out += "\n"
    out += " " + " " * max_len
    for i in range(trace_len):
        out += f" {i % 10}"
    return out + "\n"


def _marking_char(marking: bool | int) -> str:  # noqa: FBT001
    if isinstance(marking, bool):
        return "●" if marking else " "
    string = str(marking)
    return string if len(string) == 1 else "*"


LOOP_STR = "=Lasso="


def _get_loop_str(loop_start: int, max_formula_len: int, trace_len: int) -> str:
    out = f"{LOOP_STR:<{max_formula_len}}  "
    for i in range(trace_len):
        if i == loop_start and i == trace_len - 1:
            out += "⊔"
        elif i == loop_start:
            out += "└─"
        elif i == trace_len - 1:
            out += "┘"
        elif i > loop_start:
            out += "──"
        else:
            out += "  "
    return out + "\n"


def markings_to_str(
    markings: dict[m.Mtl, list[bool | int]],
    loop_start: int | None,
) -> str:
    subformulae = list(markings.keys())
    trace_len = len(markings[subformulae[0]])
    max_formula_len = max(len(m.to_string(f)) for f in subformulae)
    if loop_start is not None:
        max_formula_len = max(max_formula_len, len(LOOP_STR))
    out = _get_trace_indices_str(trace_len, max_formula_len)
    for f in reversed(subformulae):
        s = m.to_string(f)
        out += f"{s:<{max_formula_len}} "
        for marking in markings[f]:
            out += f"│{_marking_char(marking)}"
        out += "│\n"
    if loop_start is not None:
        out += _get_loop_str(loop_start, max_formula_len, trace_len)
    return out


def bool_markings_to_str(
    markings: dict[m.Mtl, list[bool]],
    loop_start: int | None,
) -> str:
    general_markings = typing.cast("dict[m.Mtl, list[bool | int]]", markings)
    return markings_to_str(general_markings, loop_start)
