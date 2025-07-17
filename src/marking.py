from typing import Optional
from enum import Enum
import collections
from src import mitl as m
from src import util


class Trace:
    def __init__(
        self,
        trace: list[dict[str, bool | int]],
        loop_start: Optional[int] = None,
    ):
        # NuXmv identifies loops by duplicating the state at the start of the loop at the end of the trace
        if loop_start is None:
            self.loop_start = self.periodic_trace_idx(trace)
            self.trace = trace[:-1]
        else:
            self.loop_start = loop_start
            self.trace = trace

    def periodic_trace_idx(self, trace) -> Optional[int]:
        if len(trace) == 0:
            return None
        last = trace[-1]
        for i in range(len(trace) - 2, -1, -1):
            if last == trace[i]:
                return i
        return None

    def __len__(self) -> int:
        return len(self.trace)

    def __getitem__(self, i) -> dict[str, bool | int]:
        return self.trace[i]

    def __iter__(self):
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
            raise ValueError(
                f"Mixed or unsupported types for variable '{var}': {values}"
            )
    return variable_types


def generate_vars(
    variable_types: dict[str, tuple[Mutability, str]], num_states: int
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
        [
            mutability == Mutability.CONSTANT
            for _, (mutability, _) in variable_types.items()
        ]
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
    if trace.loop_start is None:
        raise ValueError("Cannot identify loop in trace")
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
    filepath: str, trace: Trace, formula: m.Mitl
) -> list[m.Mitl]:
    trace_smv = generate_trace_smv(trace)
    ltlspec_smv, subformulae = m.generate_subformulae_smv(formula, len(trace))
    with open(filepath, "w") as f:
        f.write(trace_smv + "\n\n" + ltlspec_smv + "\n")
    return subformulae


def parse_nuxmv_output(
    output: str, subformulae: list[m.Mitl], num_states: int
) -> dict[m.Mitl, list[bool]]:
    lines = output.split("\n")
    lines = list(
        filter(
            lambda line: line.startswith("-- ")
            and not line.startswith(
                "-- as demonstrated by the following execution sequence"
            ),
            lines,
        )
    )
    markings: dict[m.Mitl, list[bool]] = {}
    for i, f in enumerate(subformulae):
        markings[f] = []
        for j in range(num_states):
            idx = i * num_states + j
            if lines[idx].endswith("true"):
                markings[f].append(True)
            elif lines[idx].endswith("false"):
                markings[f].append(False)
            else:
                raise ValueError(f"line '{lines[idx]}' is malformed")
    return markings


def fmt_markings(markings: dict[m.Mitl, list[bool]]) -> str:
    out = ""
    subformulae = list(markings.keys())
    max_len = max(len(m.to_string(f)) for f in subformulae)
    for f in reversed(subformulae):
        s = m.to_string(f)
        out += f"{s:<{max_len}} : "
        for marking in markings[f]:
            if marking:
                out += "X-"
            else:
                out += " -"
        out = out[:-1]
        out += "\n"
    return out[:-1]


def mark_trace(trace: Trace, formula: m.Mitl) -> dict[m.Mitl, list[bool]]:
    subformulae = write_trace_smv("res/trace.smv", trace, formula)
    out = util.run_and_capture(
        ["nuXmv", "-source", "res/check_trace.txt"], output=False
    )
    return parse_nuxmv_output(out, subformulae, len(trace))
