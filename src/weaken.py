from typing import Optional, cast

from src import marking, mitl


def get_subformula(formula: mitl.Mitl, indices: list[int]) -> mitl.Mitl:
    for i in indices:
        if isinstance(formula, mitl.Prop):
            IndexError(
                f"De Bruijn index {i} invalid for {mitl.to_string(formula)}"
            )
        if isinstance(formula, (mitl.Not, mitl.Eventually, mitl.Always)):
            if i == 0:
                formula = formula.operand
            else:
                IndexError(
                    f"De Bruijn index {i} invalid for {mitl.to_string(formula)}"
                )
        elif isinstance(formula, (mitl.And, mitl.Or, mitl.Implies, mitl.Until)):
            if i == 0:
                formula = formula.left
            elif i == 1:
                formula = formula.right
            else:
                IndexError(
                    f"De Bruijn index {i} invalid for {mitl.to_string(formula)}"
                )
        else:
            raise ValueError(f"Unsupported MITL construct: {formula}")
    return formula


class Weaken:

    def __init__(
        self,
        formula: mitl.Mitl,
        indices: list[int],
        trace: marking.Trace,
        markings: Optional[marking.Marking] = None,
    ):
        self.formula = formula
        self.indices = indices
        self.trace = trace
        self.markings = (
            marking.Marking(self.trace, self.formula)
            if markings is None
            else markings
        )
        self.trace_len = len(trace)
        self.subformula = get_subformula(formula, indices)
        if isinstance(
            self.subformula, (mitl.Always, mitl.Eventually, mitl.Until)
        ):
            self.original_interval = self.subformula.interval
        else:
            raise ValueError(
                f"Cannot weaken MITL subformula: {self.subformula}"
            )

    def interval_abs_diff(
        self,
        interval: mitl.Interval,
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

    def aux_not(
        self, formula: mitl.Not, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        raise NotImplementedError("")

    def aux_and(
        self, formula: mitl.And, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if self.indices[formula_idx] == 0:
            if not self.markings.markings[formula.right][trace_idx]:
                return None
            return self.aux(formula.left, trace_idx, formula_idx + 1)
        if self.indices[formula_idx] == 1:
            if not self.markings.markings[formula.left][trace_idx]:
                return None
            return self.aux(formula.right, trace_idx, formula_idx + 1)
        raise IndexError(
            f"De Bruijn index {formula_idx} invalid for {mitl.to_string(formula)}"
        )

    def aux_or(
        self, formula: mitl.Or, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if self.indices[formula_idx] == 0:
            if self.markings[formula.right][trace_idx]:
                return self.original_interval
            return self.aux(formula.left, trace_idx, formula_idx + 1)
        if self.indices[formula_idx] == 1:
            if self.markings[formula.left][trace_idx]:
                return self.original_interval
            return self.aux(formula.right, trace_idx, formula_idx + 1)
        raise IndexError(
            f"De Bruijn index {formula_idx} invalid for {mitl.to_string(formula)}"
        )

    def aux_implies(
        self, formula: mitl.Implies, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        raise NotImplementedError("")

    def weaken_eventually(
        self, formula: mitl.Eventually, trace_idx: int
    ) -> Optional[mitl.Interval]:
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of F[{a}, ∞)")
        for i in range(a, self.trace_len):
            if self.markings[formula.operand][self.trace.idx(trace_idx + i)]:
                return a, max(b, i)
        return None

    def aux_eventually(
        self, formula: mitl.Eventually, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if formula_idx == len(self.indices):
            return self.weaken_eventually(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        all_intervals = [
            self.aux(formula.operand, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=self.interval_abs_diff)

    def weaken_always(self, formula: mitl.Always, trace_idx: int):
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        # Expand the interval until we find a state when the operand is false,
        # then reduce the interval to just before that
        for i in range(a, right_idx):
            if not self.markings[formula.operand][
                self.trace.idx(trace_idx + i)
            ]:
                if i == a:
                    return None
                return a, i - 1
        return a, b

    def aux_always(
        self, formula: mitl.Always, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if formula_idx == len(self.indices):
            return self.weaken_always(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        intervals = []
        for i in range(a, right_idx):
            interval = self.aux(formula.operand, trace_idx + i, formula_idx + 1)
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=self.interval_abs_diff)

    def weaken_until(self, formula: mitl.Until, trace_idx: int):
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of U[{a}, ∞)")
        for i in range(a, self.trace_len):
            if self.markings[formula.right][self.trace.idx(trace_idx + i)]:
                return a, max(b, i)
            if not self.markings[formula.left][self.trace.idx(trace_idx + i)]:
                break
        return None

    def aux_until_left(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        raise NotImplementedError("")

    def aux_until_right(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        all_intervals = [
            self.aux(formula.right, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        valid_intervals: list[Optional[mitl.Interval]] = []
        for i in range(a, right_idx):
            valid_intervals.append(all_intervals[i])
            if not self.markings[formula.left][self.trace.idx(trace_idx + i)]:
                break
        intervals = [i for i in valid_intervals if i is not None]
        return min(intervals, key=self.interval_abs_diff)

    def aux_until(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if formula_idx == len(self.indices):
            return self.weaken_until(formula, trace_idx)
        if self.indices[formula_idx] == 0:
            return self.aux_until_left(formula, trace_idx, formula_idx)
        if self.indices[formula_idx] == 1:
            return self.aux_until_right(formula, trace_idx, formula_idx)
        raise IndexError(
            f"De Bruijn index {formula_idx} invalid for {mitl.to_string(formula)}"
        )

    def aux(
        self, formula: mitl.Mitl, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        assert formula_idx <= len(self.indices)
        if isinstance(formula, mitl.Prop):
            return None
        if isinstance(formula, mitl.Not):
            return self.aux_not(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.And):
            return self.aux_and(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Or):
            return self.aux_or(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Implies):
            return self.aux_implies(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Eventually):
            return self.aux_eventually(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Always):
            return self.aux_always(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Until):
            return self.aux_until(formula, trace_idx, formula_idx)
        raise ValueError(f"Unsupported MITL construct: {formula}")

    def weaken(self) -> Optional[mitl.Interval]:
        return self.aux(self.formula, 0, 0)
