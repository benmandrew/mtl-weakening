from typing import cast

from src import marking
from src.logic import ctx, mtl


class Weaken:
    """
    Performs trace-guided interval weakening of MTL subformulas.

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
    ):
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
        if isinstance(
            self.subformula,
            (mtl.Always, mtl.Eventually, mtl.Until),
        ):
            self.original_interval = self.subformula.interval
        else:
            raise ValueError(f"Cannot weaken MTL subformula: {self.subformula}")

    def _interval_abs_diff(
        self,
        interval: mtl.Interval,
    ) -> int:
        if self.original_interval[1] is None and interval[1] is None:
            right = 0
        elif self.original_interval[1] is None:
            right = -cast(int, interval[1])
        else:
            right = abs(
                cast(int, interval[1]) - cast(int, self.original_interval[1])
            )
        return abs(interval[0] - self.original_interval[0]) + right

    def _aux_and(
        self, c: ctx.Ctx, f: mtl.Mtl, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside conjunction.
        """
        if not self.markings.get(f, trace_idx):
            return None
        return self._aux(c, trace_idx)

    def _aux_or(
        self, c: ctx.Ctx, f: mtl.Mtl, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside disjunction.
        """
        if self.markings.get(f, trace_idx):
            return self.original_interval
        return self._aux(c, trace_idx)

    def _aux_implies_left(
        self, c: ctx.ImpliesLeft, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside implication.
        """
        return self._aux_or(ctx.Not(c.left), c.right, trace_idx)

    def _aux_implies_right(
        self, c: ctx.ImpliesRight, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside implication.
        """
        return self._aux_or(c.right, mtl.Not(c.left), trace_idx)

    def _aux_eventually(
        self, c: ctx.Eventually, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside eventually operator.
        """
        a, b = c.interval
        right_idx = self.trace_len if b is None else b + 1
        all_intervals = [
            self._aux(c.operand, trace_idx + i) for i in range(a, right_idx)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=self._interval_abs_diff)

    def _aux_always(self, c: ctx.Always, trace_idx: int) -> mtl.Interval | None:
        """
        Weakening inside always operator.
        """
        a, b = c.interval
        right_idx = self.trace_len if b is None else b + 1
        intervals = []
        for i in range(a, right_idx):
            interval = self._aux(c.operand, trace_idx + i)
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=self._interval_abs_diff)

    def _aux_until_left(
        self, c: ctx.UntilLeft, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside until operator.
        """
        a, b = c.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        all_intervals = [
            self._aux(c.left, trace_idx + i) for i in range(a, right_idx)
        ]
        valid_intervals = []
        for i, interval in enumerate(all_intervals):
            if interval is None:
                break
            if not self.markings.get(c.right, trace_idx + i + a):
                continue
            valid_intervals.append(interval)
        intervals = [i for i in valid_intervals if i is not None]
        if not intervals:
            return None
        return max(intervals, key=self._interval_abs_diff)

    def _aux_until_right(
        self, c: ctx.UntilRight, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside until operator.
        """
        a, b = c.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        valid_intervals: list[mtl.Interval | None] = []
        for i in range(a, right_idx):
            valid_intervals.append(self._aux(c.right, trace_idx + i))
            if not self.markings.get(c.left, trace_idx + i):
                break
        intervals = [i for i in valid_intervals if i is not None]
        if not intervals:
            return None
        return min(intervals, key=self._interval_abs_diff)

    def _naux_and(
        self, c: ctx.Ctx, f: mtl.Mtl, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside conjunction in negative polarity.
        """
        if self.markings.get(f, trace_idx):
            return self.original_interval
        return self._naux(c, trace_idx)

    def _naux_or(
        self, c: ctx.Ctx, f: mtl.Mtl, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside disjunction in negative polarity.
        """
        if not self.markings.get(f, trace_idx):
            return None
        return self._aux(c, trace_idx)

    def _naux_implies_left(
        self, c: ctx.ImpliesLeft, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside implication implication in negative polarity by .
        """
        return self._naux_or(ctx.Not(c.left), c.right, trace_idx)

    def _naux_implies_right(
        self, c: ctx.ImpliesRight, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside implication implication in negative polarity by .
        """
        return self._naux_or(c.right, mtl.Not(c.left), trace_idx)

    def _naux_eventually(
        self, c: ctx.Eventually, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside eventually operator in negative polarity.
        """
        a, b = c.interval
        right_idx = self.trace_len if b is None else b + 1
        intervals = []
        for i in range(a, right_idx):
            interval = self._naux(c.operand, trace_idx + i)
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=self._interval_abs_diff)

    def _naux_always(
        self, c: ctx.Always, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside always operator in negative polarity.
        """
        a, b = c.interval
        right_idx = self.trace_len if b is None else b + 1
        all_intervals = [
            self._naux(c.operand, trace_idx + i) for i in range(a, right_idx)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=self._interval_abs_diff)

    def _naux_until_left(
        self, c: ctx.UntilLeft, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside until operator in negative polarity.
        """
        raise NotImplementedError()

    def _naux_until_right(
        self, c: ctx.UntilRight, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside until operator in negative polarity.
        """
        raise NotImplementedError()

    def _weaken_direct_eventually(
        self, f: mtl.Eventually, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Directly weaken interval of eventually operator.
        """
        a, b = f.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of F[{a}, ∞)")
        # Expand the interval until we find a state when the operand is true
        for i in range(a, self.trace_len * 2):
            if self.markings.get(f.operand, trace_idx + i):
                return a, max(b, i)
        return None

    def _weaken_direct_always(
        self, f: mtl.Always, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Directly weaken interval of always operator.
        """
        a, b = f.interval
        right_idx = self.trace_len if b is None else b + 1
        # Expand the interval until we find a state when the operand is false,
        # then reduce the interval to just before that
        for i in range(a, right_idx):
            if not self.markings.get(f.operand, trace_idx + i):
                if i == a:
                    return None
                return a, i - 1
        return a, b

    def _weaken_direct_until(self, f: mtl.Until, trace_idx: int):
        """
        Directly weaken interval of until operator.
        """
        a, b = f.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of U[{a}, ∞)")
        for i in range(a, self.trace_len * 2):
            if self.markings.get(f.right, trace_idx + i):
                return a, max(b, i)
            if not self.markings.get(f.left, trace_idx + i):
                break
        return None

    def _weaken_direct(self, trace_idx: int) -> mtl.Interval | None:
        if isinstance(self.subformula, mtl.Eventually):
            return self._weaken_direct_eventually(self.subformula, trace_idx)
        if isinstance(self.subformula, mtl.Always):
            return self._weaken_direct_always(self.subformula, trace_idx)
        if isinstance(self.subformula, mtl.Until):
            return self._weaken_direct_until(self.subformula, trace_idx)
        raise ValueError(f"Cannot weaken MTL subformula: {self.subformula}")

    def _nweaken_direct_eventually(
        self, f: mtl.Eventually, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Directly weaken interval of eventually operator in negative polarity.
        """
        a, b = f.interval
        right_idx = self.trace_len if b is None else b + 1
        # Expand the interval until we find a state when the operand is true
        # then reduce the interval to just before that
        for i in range(a, right_idx):
            if self.markings.get(f.operand, trace_idx + i):
                if i == a:
                    return None
                return a, i - 1
        return a, b

    def _nweaken_direct_always(
        self, f: mtl.Always, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Directly weaken interval of always operator in negative polarity.
        """
        a, b = f.interval
        if b is None:
            raise ValueError(
                f"Cannot weaken interval of G[{a}, ∞) in negative polarity"
            )
        # Expand the interval until we find a state when the operand is true,
        # then reduce the interval to just before that
        for i in range(a, self.trace_len * 2):
            if not self.markings.get(f.operand, trace_idx + i):
                return a, max(b, i)
        return None

    def _nweaken_direct_until(self, f: mtl.Until, trace_idx: int):
        """
        Directly weaken interval of until operator in negative polarity.
        """
        raise NotImplementedError("")

    def _nweaken_direct(self, trace_idx: int) -> mtl.Interval | None:
        if isinstance(self.subformula, mtl.Eventually):
            return self._nweaken_direct_eventually(self.subformula, trace_idx)
        if isinstance(self.subformula, mtl.Always):
            return self._nweaken_direct_always(self.subformula, trace_idx)
        if isinstance(self.subformula, mtl.Until):
            return self._nweaken_direct_until(self.subformula, trace_idx)
        raise ValueError(f"Cannot weaken MTL subformula: {self.subformula}")

    def _aux(self, c: ctx.Ctx, trace_idx: int) -> mtl.Interval | None:
        """
        Recursively weakens subformulas in positive polarity.

        Follows the De Bruijn index to the target subformula. If the
        index matches, the corresponding `_weaken_*` method is applied.

        Otherwise, recursion proceeds through `_aux_*` operator-specific
        handlers. Negations flip polarity and delegate to `_naux`.
        """
        if isinstance(c, ctx.Hole):
            return self._weaken_direct(trace_idx)
        if isinstance(c, ctx.Not):
            return self._naux(c.operand, trace_idx)
        if isinstance(c, ctx.AndLeft):
            return self._aux_and(c.left, c.right, trace_idx)
        if isinstance(c, ctx.AndRight):
            return self._aux_and(c.right, c.left, trace_idx)
        if isinstance(c, ctx.OrLeft):
            return self._aux_or(c.left, c.right, trace_idx)
        if isinstance(c, ctx.OrRight):
            return self._aux_or(c.right, c.left, trace_idx)
        if isinstance(c, ctx.ImpliesLeft):
            return self._aux_implies_left(c, trace_idx)
        if isinstance(c, ctx.ImpliesRight):
            return self._aux_implies_right(c, trace_idx)
        if isinstance(c, ctx.Eventually):
            return self._aux_eventually(c, trace_idx)
        if isinstance(c, ctx.Always):
            return self._aux_always(c, trace_idx)
        if isinstance(c, ctx.UntilLeft):
            return self._aux_until_left(c, trace_idx)
        if isinstance(c, ctx.UntilRight):
            return self._aux_until_right(c, trace_idx)
        raise ValueError(f"Unsupported MTL context construct: {c}")

    def _naux(self, c: ctx.Ctx, trace_idx: int) -> mtl.Interval | None:
        """
        Recursively weakens subformulas in negative polarity.

        Operates under negation, treating each operator via `_naux_*`
        methods. A nested negation flips polarity back to `_aux`.

        This structure mirrors the NNF of the formula and ensures
        dual-handling of temporal and boolean constructs.
        """
        if isinstance(c, ctx.Hole):
            return self._nweaken_direct(trace_idx)
        if isinstance(c, ctx.Not):
            return self._aux(c.operand, trace_idx)
        if isinstance(c, ctx.AndLeft):
            return self._naux_and(c.left, c.right, trace_idx)
        if isinstance(c, ctx.AndRight):
            return self._naux_and(c.right, c.left, trace_idx)
        if isinstance(c, ctx.OrLeft):
            return self._naux_or(c.left, c.right, trace_idx)
        if isinstance(c, ctx.OrRight):
            return self._naux_or(c.right, c.left, trace_idx)
        if isinstance(c, ctx.ImpliesLeft):
            return self._naux_implies_left(c, trace_idx)
        if isinstance(c, ctx.ImpliesRight):
            return self._naux_implies_right(c, trace_idx)
        if isinstance(c, ctx.Eventually):
            return self._naux_eventually(c, trace_idx)
        if isinstance(c, ctx.Always):
            return self._naux_always(c, trace_idx)
        if isinstance(c, ctx.UntilLeft):
            return self._naux_until_left(c, trace_idx)
        if isinstance(c, ctx.UntilRight):
            return self._naux_until_right(c, trace_idx)
        raise ValueError(f"Unsupported MTL context construct: {c}")

    def weaken(self) -> mtl.Interval | None:
        return self._aux(self.context, 0)
