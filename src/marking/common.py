import typing

from src.logic import mtl as m


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


class ExtendedDict:
    """Either a dict, or default True."""

    def __init__(self, d: dict[str, bool | int | str] | None) -> None:
        self.d = d

    def __getitem__(self, k: str) -> bool | int | str:
        if self.d:
            return self.d.get(k, True)
        return True

    def __setitem__(self, k: str, v: bool | int | str) -> None:
        if self.d is not None:
            self.d[k] = v

    def __contains__(self, k: str) -> bool:
        if self.d is None:
            return True
        return k in self.d


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
        loop_start: int | None,
    ) -> None:
        trace = expand_nuxmv_trace(trace)
        assert loop_start is None or loop_start < len(trace)
        self.loop_start = loop_start
        self.trace = trace

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

    def idx(self, i: int) -> int:
        if self.loop_start is None:
            assert i < len(self.trace)
            return i
        if i >= len(self.trace):
            j = (i - self.loop_start) % (len(self.trace) - self.loop_start)
            return j + self.loop_start
        return i

    def right_idx(self, a: int) -> int:
        """Get the index of the right side of the trace."""
        if self.loop_start is None or a < self.loop_start:
            return len(self.trace) - 1
        suf_len = len(self.trace) - self.loop_start
        return a + suf_len - 1

    def __len__(self) -> int:
        return len(self.trace)

    def __getitem__(self, i: int) -> ExtendedDict:
        if self.loop_start is None and i >= len(self.trace):
            return ExtendedDict(None)
        return ExtendedDict(self.trace[self.idx(i)])

    def __iter__(self) -> typing.Iterator[dict[str, bool | int | str]]:
        return iter(self.trace)
