from __future__ import annotations

import collections
import logging
import typing
from dataclasses import dataclass
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


@dataclass
class Finite:
    pass


@dataclass
class Lasso:
    loop_start: int


Finiteness = Finite | Lasso


class Trace:
    def __init__(
        self,
        trace: list[dict[str, bool | int | str]],
        loop_start: int | None = None,
    ) -> None:
        trace = expand_nuxmv_trace(trace)
        if loop_start is None:
            loop_start = self.periodic_trace_idx(trace)
            if loop_start is None:
                self.finiteness: Finiteness = Finite()
                self.trace = trace
            else:
                self.finiteness = Lasso(loop_start)
                self.trace = trace[:-1]
        else:
            assert loop_start < len(trace)
            self.finiteness = Lasso(loop_start)
            self.trace = trace

    def to_markings(self) -> dict[m.Mtl, list[bool]]:
        markings: dict[m.Mtl, list[bool]] = {}
        for state in self.trace:
            for k, v in state.items():
                if type(v) is not bool:
                    continue
                f = m.Prop(k)
                if f not in markings:
                    markings[f] = []
                markings[f].append(v)
        return markings

    def periodic_trace_idx(
        self,
        trace: list[dict[str, bool | int | str]],
    ) -> int | None:
        """
        Attempts to find the start of a loop in the trace.
        If none is found, then None is returned.

        NuXmv identifies loops by duplicating the state
        at the start of the loop at the end of the trace.
        """
        if len(trace) > 0:
            last = trace[-1]
            for i in range(len(trace) - 2, -1, -1):
                if last == trace[i]:
                    return i
        logger.debug("Cannot identify loop in trace, assuming finite")
        return None

    def idx(self, i: int) -> int:
        if isinstance(self.finiteness, Finite):
            assert i < len(self.trace)
            return i
        if i >= len(self.trace):
            j = (i - self.finiteness.loop_start) % (
                len(self.trace) - self.finiteness.loop_start
            )
            return j + self.finiteness.loop_start
        return i

    def right_idx(self, a: int) -> int:
        """Get the index of the right side of the trace."""
        if (
            isinstance(self.finiteness, Finite)
            or a < self.finiteness.loop_start
        ):
            return len(self.trace) - 1
        suf_len = len(self.trace) - self.finiteness.loop_start
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
        self.markings = trace.to_markings()
        self[formula]

    def add_loop_str(self, max_len: int) -> str:
        assert isinstance(self.trace.finiteness, Lasso)
        out = f"{self.loop_str:<{max_len}}  "
        loop_start = self.trace.finiteness.loop_start
        for i in range(len(self.trace)):
            if i == loop_start and i == len(self.trace) - 1:
                out += "⊔"
            elif i == loop_start:
                out += "└─"
            elif i == len(self.trace) - 1:
                out += "┘"
            elif i > loop_start:
                out += "──"
            else:
                out += "  "
        return out

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
        for i in range(len(bs)):
            right_idx = interval[1] + 1 if interval[1] is not None else len(vs)
            bs[i] = any(
                vs[self.trace.idx(j)]
                for j in range(i + interval[0], i + right_idx)
            )
        return bs

    def _get_always(self, operand: m.Mtl, interval: m.Interval) -> list[bool]:
        vs = self[operand]
        bs = [False] * len(vs)
        for i in range(len(bs)):
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
        for i in range(len(bs)):
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
        for i in range(len(bs)):
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

    def __getitem__(self, f: m.Mtl) -> list[bool]:
        if f in self.markings:
            return self.markings[f]
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
        if isinstance(self.trace.finiteness, Lasso):
            out += self.add_loop_str(max_len)
        return out
