from __future__ import annotations

from typing import cast

from src import marking
from src.logic import ctx, mtl


class Weaken:
    """Performs trace-guided interval weakening of MTL subformulas.

    Weakening is done by adjusting the interval so that the modified
    formula remains true over the given trace.

    The algorithm is mutually recursive, alternating between `_aux` and
    `_naux` depending on polarity. Negations reverse polarity and
    delegate to the corresponding opposite method.

    Temporal operators use specific `_weaken_*` methods to attempt
    interval expansion while preserving validity over the trace.
    """

    def __init__(
        self,
        context: ctx.Ctx,
        subformula: mtl.Mtl,
        trace: marking.Trace,
        markings: marking.Marking | None = None,
    ) -> None:
        self.context = context
        self.subformula = subformula
        self.trace = trace
        formula = ctx.substitute(context, subformula)
        self.markings = (
            marking.Marking(self.trace, formula)
            if markings is None
            else markings
        )
        self.trace_len = len(trace)
        if not isinstance(
            self.subformula,
            (mtl.Always, mtl.Eventually, mtl.Until, mtl.Release),
        ):
            msg = f"Cannot weaken MTL subformula: {self.subformula}"
            raise TypeError(msg)
        self.original_interval = self.subformula.interval

    def _interval_abs_diff(
        self,
        interval: mtl.Interval,
    ) -> int:
        if self.original_interval[1] is None and interval[1] is None:
            right = 0
        elif self.original_interval[1] is None:
            right = -cast("int", interval[1])
        else:
            right = abs(
                cast("int", interval[1])
                - cast("int", self.original_interval[1]),
            )
        return abs(interval[0] - self.original_interval[0]) + right

    def _aux_and(
        self,
        c: ctx.Ctx,
        f: mtl.Mtl,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Weakening inside conjunction."""
        if not self.markings.get(f, trace_idx):
            return None
        return self._aux(c, trace_idx)

    def _aux_or(
        self,
        c: ctx.Ctx,
        f: mtl.Mtl,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Weakening inside disjunction."""
        if self.markings.get(f, trace_idx):
            return self.original_interval
        return self._aux(c, trace_idx)

    def _aux_eventually(
        self,
        c: ctx.Eventually,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Weakening inside eventually operator."""
        a, b = c.interval
        right_idx = self.trace.right_idx(a) if b is None else b
        all_intervals = [
            self._aux(c.operand, trace_idx + i) for i in range(a, right_idx + 1)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=self._interval_abs_diff)

    def _aux_always(self, c: ctx.Always, trace_idx: int) -> mtl.Interval | None:
        """Weakening inside always operator."""
        a, b = c.interval
        right_idx = self.trace.right_idx(a) if b is None else b
        intervals = []
        for i in range(a, right_idx + 1):
            interval = self._aux(c.operand, trace_idx + i)
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=self._interval_abs_diff)

    def _aux_until_left(
        self,
        c: ctx.UntilLeft,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Weakening inside until operator."""
        a, b = c.interval
        right_idx = self.trace.right_idx(a) if b is None else b
        intervals: list[mtl.Interval] = []
        for i in range(a, right_idx + 1):
            interval = self._aux(c.left, trace_idx + i)
            if interval is None:
                return None
            if self.markings.get(c.right, trace_idx + i):
                break
            intervals.append(interval)
        if not intervals:
            return self.original_interval
        return max(intervals, key=self._interval_abs_diff)

    def _aux_until_right(
        self,
        c: ctx.UntilRight,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Weakening inside until operator."""
        a, b = c.interval
        right_idx = self.trace.right_idx(a) if b is None else b
        intervals: list[mtl.Interval] = []
        for i in range(a, right_idx + 1):
            interval = self._aux(c.right, trace_idx + i)
            if interval is not None:
                intervals.append(interval)
            if not self.markings.get(c.left, trace_idx + i):
                break
        if not intervals:
            return None
        return min(intervals, key=self._interval_abs_diff)

    def _aux_release_left(
        self,
        c: ctx.ReleaseLeft,
        trace_idx: int,
    ) -> mtl.Interval | None:
        a, b = c.interval
        right_idx = self.trace.right_idx(a) if b is None else b
        intervals: list[mtl.Interval] = []
        for i in range(a, right_idx + 1):
            if not self.markings.get(c.right, trace_idx + i):
                break
            interval = self._aux(c.left, trace_idx + i)
            if interval is not None:
                intervals.append(interval)
        if not intervals:
            return None
        return min(intervals, key=self._interval_abs_diff)

    def _aux_release_right(
        self,
        c: ctx.ReleaseRight,
        trace_idx: int,
    ) -> mtl.Interval | None:
        a, b = c.interval
        right_idx = self.trace.right_idx(a) if b is None else b
        intervals: list[mtl.Interval] = []
        for i in range(a, right_idx + 1):
            interval = self._aux(c.right, trace_idx + i)
            if interval is None or self.markings.get(c.left, trace_idx + i + a):
                break
            intervals.append(interval)
        if not intervals:
            return None
        return max(intervals, key=self._interval_abs_diff)

    def _weaken_direct_eventually(
        self,
        f: mtl.Eventually,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Directly weaken interval of eventually operator."""
        a, b = f.interval
        if b is None:
            msg = f"Cannot weaken interval of F[{a}, ∞)"
            raise ValueError(msg)
        # Expand the interval until we find a state when the operand is true
        for i in range(a, self.trace.right_idx(a) + 1):
            if self.markings.get(f.operand, trace_idx + i):
                return a, max(b, i)
        return None

    def _weaken_direct_always(
        self,
        f: mtl.Always,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Directly weaken interval of always operator."""
        a, b = f.interval
        # Expand the interval until we find a state when the operand is false,
        # then reduce the interval to just before that
        right_idx = self.trace.right_idx(a) if b is None else b
        for i in range(a, right_idx + 1):
            if not self.markings.get(f.operand, trace_idx + i):
                if i == a:
                    return None
                return a, i - 1
        return a, b

    def _weaken_direct_until(
        self,
        f: mtl.Until,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Directly weaken interval of until operator."""
        a, b = f.interval
        if b is None:
            msg = f"Cannot weaken interval of U[{a}, ∞)"
            raise ValueError(msg)
        for i in range(a, self.trace.right_idx(a) + 1):
            if self.markings.get(f.right, trace_idx + i):
                return a, max(b, i)
            if not self.markings.get(f.left, trace_idx + i):
                break
        return None

    def _weaken_direct_release(
        self,
        f: mtl.Release,
        trace_idx: int,
    ) -> mtl.Interval | None:
        """Directly weaken interval of release operator."""
        a, b = f.interval
        right_idx = self.trace.right_idx(a) if b is None else b
        for i in range(a, right_idx + 1):
            if not self.markings.get(f.right, trace_idx + i):
                if i == a:
                    return None
                return a, i - 1
            if self.markings.get(f.left, trace_idx + i):
                return a, b
        return a, b

    def _weaken_direct(self, trace_idx: int) -> mtl.Interval | None:
        if isinstance(self.subformula, mtl.Eventually):
            return self._weaken_direct_eventually(self.subformula, trace_idx)
        if isinstance(self.subformula, mtl.Always):
            return self._weaken_direct_always(self.subformula, trace_idx)
        if isinstance(self.subformula, mtl.Until):
            return self._weaken_direct_until(self.subformula, trace_idx)
        if isinstance(self.subformula, mtl.Release):
            return self._weaken_direct_release(self.subformula, trace_idx)
        msg = f"Cannot weaken MTL subformula: {self.subformula}"
        raise ValueError(msg)

    def _aux(self, c: ctx.Ctx, trace_idx: int) -> mtl.Interval | None:
        """Recursively weakens subformulas"""
        if isinstance(c, ctx.Hole):
            return self._weaken_direct(trace_idx)
        if isinstance(c, ctx.AndLeft):
            return self._aux_and(c.left, c.right, trace_idx)
        if isinstance(c, ctx.AndRight):
            return self._aux_and(c.right, c.left, trace_idx)
        if isinstance(c, ctx.OrLeft):
            return self._aux_or(c.left, c.right, trace_idx)
        if isinstance(c, ctx.OrRight):
            return self._aux_or(c.right, c.left, trace_idx)
        if isinstance(c, ctx.Eventually):
            return self._aux_eventually(c, trace_idx)
        if isinstance(c, ctx.Always):
            return self._aux_always(c, trace_idx)
        if isinstance(c, ctx.UntilLeft):
            return self._aux_until_left(c, trace_idx)
        if isinstance(c, ctx.UntilRight):
            return self._aux_until_right(c, trace_idx)
        if isinstance(c, ctx.ReleaseLeft):
            return self._aux_release_left(c, trace_idx)
        if isinstance(c, ctx.ReleaseRight):
            return self._aux_release_right(c, trace_idx)
        msg = f"Unsupported MTL context construct: {c}"
        raise ValueError(msg)

    def weaken(self) -> mtl.Interval | None:
        return self._aux(self.context, 0)
