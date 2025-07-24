from typing import cast

from src import marking, mitl


def get_subformula(formula: mitl.Mitl, indices: list[int]) -> mitl.Mitl:
    for i in indices:
        if isinstance(formula, mitl.Prop):
            mitl.DeBruijnIndexError(indices, i, formula)
        if isinstance(formula, (mitl.Not, mitl.Eventually, mitl.Always)):
            if i == 0:
                formula = formula.operand
            else:
                mitl.DeBruijnIndexError(indices, i, formula)
        elif isinstance(formula, (mitl.And, mitl.Or, mitl.Implies, mitl.Until)):
            if i == 0:
                formula = formula.left
            elif i == 1:
                formula = formula.right
            else:
                mitl.DeBruijnIndexError(indices, i, formula)
        else:
            raise ValueError(f"Unsupported MITL construct: {formula}")
    return formula


# Return a tuple of the left and right operands of a binary formula,
# with the first operand being the one at the De Bruijn index.
def get_de_bruijn_binary(
    formula: mitl.And | mitl.Or | mitl.Implies | mitl.Until | mitl.Release,
    indices: list[int],
    formula_idx: int,
) -> tuple[mitl.Mitl, mitl.Mitl]:
    if indices[formula_idx] == 0:
        return formula.left, formula.right
    if indices[formula_idx] == 1:
        return formula.right, formula.left
    raise mitl.DeBruijnIndexError(indices, formula_idx, formula)


class Weaken:

    def __init__(
        self,
        formula: mitl.Mitl,
        indices: list[int],
        trace: marking.Trace,
        markings: marking.Marking | None = None,
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

    # Weakening inside conjunction
    def _aux_and(
        self, formula: mitl.And, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if not self.markings.get(secondary, trace_idx):
            return None
        return self._aux(primary, trace_idx, formula_idx + 1)

    # Weakening inside conjunction within negation
    def _naux_and(
        self, formula: mitl.And, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if self.markings.get(secondary, trace_idx):
            return self.original_interval
        return self._naux(primary, trace_idx, formula_idx + 1)

    # Weakening inside disjunction
    def _aux_or(
        self, formula: mitl.Or, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if self.markings.get(secondary, trace_idx):
            return self.original_interval
        return self._aux(primary, trace_idx, formula_idx + 1)

    # Weakening inside disjunction within negation
    def _naux_or(
        self, formula: mitl.Or, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if not self.markings.get(secondary, trace_idx):
            return None
        return self._naux(primary, trace_idx, formula_idx + 1)

    # Weakening inside implication by rewriting it as a disjunction
    def _aux_implies(
        self, formula: mitl.Implies, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        return self._aux(
            mitl.Or(mitl.Not(formula.left), formula.right),
            trace_idx,
            formula_idx,
        )

    # Weakening implication within negation by rewriting it as a disjunction
    def _naux_implies(
        self, formula: mitl.Implies, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        return self._naux(
            mitl.Or(mitl.Not(formula.left), formula.right),
            trace_idx,
            formula_idx,
        )

    # Directly weaken the interval of the eventually operator
    def _weaken_eventually(
        self, formula: mitl.Eventually, trace_idx: int
    ) -> mitl.Interval | None:
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of F[{a}, ∞)")
        for i in range(a, self.trace_len * 2):
            if self.markings.get(formula.operand, trace_idx + i):
                return a, max(b, i)
        return None

    # Directly weaken interval of eventually operator within negation
    def _nweaken_eventually(
        self, formula: mitl.Eventually, trace_idx: int
    ) -> mitl.Interval | None:
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        # Expand the interval until we find a state when the operand is false,
        # then reduce the interval to just before that
        for i in range(a, right_idx):
            if not self.markings.get(formula.operand, trace_idx + i):
                if i == a:
                    return None
                return a, i - 1
        return a, b

    # Weakening inside eventually operator
    def _aux_eventually(
        self, formula: mitl.Eventually, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        if formula_idx == len(self.indices):
            return self._weaken_eventually(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        all_intervals = [
            self._aux(formula.operand, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=self.interval_abs_diff)

    # Weakening inside eventually operator within negation
    def _naux_eventually(
        self, formula: mitl.Eventually, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        if formula_idx == len(self.indices):
            return self._nweaken_eventually(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        intervals = []
        for i in range(a, right_idx):
            interval = self._naux(
                formula.operand, trace_idx + i, formula_idx + 1
            )
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=self.interval_abs_diff)

    # Directly weaken the interval of the always operator
    def _weaken_always(self, formula: mitl.Always, trace_idx: int):
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        # Expand the interval until we find a state when the operand is false,
        # then reduce the interval to just before that
        for i in range(a, right_idx):
            if not self.markings.get(formula.operand, trace_idx + i):
                if i == a:
                    return None
                return a, i - 1
        return a, b

    # Directly weaken interval of always operator inside negation
    def _nweaken_always(self, formula: mitl.Always, trace_idx: int):
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of F[{a}, ∞)")
        for i in range(a, self.trace_len * 2):
            if self.markings.get(formula.operand, trace_idx + i):
                return a, max(b, i)
        return None

    # Weakening inside always operator
    def _aux_always(
        self, formula: mitl.Always, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        if formula_idx == len(self.indices):
            return self._weaken_always(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        intervals = []
        for i in range(a, right_idx):
            interval = self._aux(
                formula.operand, trace_idx + i, formula_idx + 1
            )
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=self.interval_abs_diff)

    # Weakening inside always operator within negation
    def _naux_always(
        self, formula: mitl.Always, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        if formula_idx == len(self.indices):
            return self._nweaken_always(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        all_intervals = [
            self._naux(formula.operand, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=self.interval_abs_diff)

    # Directly weaken interval of until operator
    def _weaken_until(self, formula: mitl.Until, trace_idx: int):
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of U[{a}, ∞)")
        for i in range(a, self.trace_len * 2):
            if self.markings.get(formula.right, trace_idx + i):
                return a, max(b, i)
            if not self.markings.get(formula.left, trace_idx + i):
                break
        return None

    # Directly weaken interval of until operator within negation
    def _nweaken_until(self, formula: mitl.Until, trace_idx: int):
        raise NotImplementedError("")

    # Weakening inside until operator on the left side
    def _aux_until_left(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        all_intervals = [
            self._aux(formula.left, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        valid_intervals = []
        for i, interval in enumerate(all_intervals):
            if interval is None:
                break
            if not self.markings.get(formula.right, trace_idx + i + a):
                continue
            valid_intervals.append(interval)
        intervals = [i for i in valid_intervals if i is not None]
        if not intervals:
            return None
        return max(intervals, key=self.interval_abs_diff)

    # Weakening inside until operator on the left side within negation
    def _naux_until_left(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ):
        raise NotImplementedError("")

    # Weakening inside until operator on the right side
    def _aux_until_right(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        valid_intervals: list[mitl.Interval | None] = []
        for i in range(a, right_idx):
            valid_intervals.append(
                self._aux(formula.right, trace_idx + i, formula_idx + 1)
            )
            if not self.markings.get(formula.left, trace_idx + i):
                break
        intervals = [i for i in valid_intervals if i is not None]
        if not intervals:
            return None
        return min(intervals, key=self.interval_abs_diff)

    # Weakening inside until operator on the right side within negation
    def _naux_until_right(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ):
        raise NotImplementedError("")

    # Weakening inside until operator
    def _aux_until(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        if formula_idx == len(self.indices):
            return self._weaken_until(formula, trace_idx)
        if self.indices[formula_idx] == 0:
            return self._aux_until_left(formula, trace_idx, formula_idx)
        if self.indices[formula_idx] == 1:
            return self._aux_until_right(formula, trace_idx, formula_idx)
        raise mitl.DeBruijnIndexError(self.indices, formula_idx, formula)

    # Weakening inside until operator within negation
    def _naux_until(
        self, formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        if formula_idx == len(self.indices):
            return self._nweaken_until(formula, trace_idx)
        if self.indices[formula_idx] == 0:
            return self._naux_until_left(formula, trace_idx, formula_idx)
        if self.indices[formula_idx] == 1:
            return self._naux_until_right(formula, trace_idx, formula_idx)
        raise mitl.DeBruijnIndexError(self.indices, formula_idx, formula)

    # Weakening inside release operator
    def _aux_release(
        self, formula: mitl.Release, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        raise NotImplementedError("")

    # Weakening inside Release operator within negation
    def _naux_release(
        self, formula: mitl.Release, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        raise NotImplementedError("")

    # Weaken inside MITL formula
    def _aux(
        self, formula: mitl.Mitl, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        assert formula_idx <= len(self.indices)
        if isinstance(formula, mitl.Prop):
            return None
        if isinstance(formula, mitl.Not):
            return self._naux(formula.operand, trace_idx, formula_idx)
        if isinstance(formula, mitl.And):
            return self._aux_and(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Or):
            return self._aux_or(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Implies):
            return self._aux_implies(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Eventually):
            return self._aux_eventually(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Always):
            return self._aux_always(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Until):
            return self._aux_until(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Release):
            return self._aux_release(formula, trace_idx, formula_idx)
        raise ValueError(f"Unsupported MITL construct: {formula}")

    # Weaken inside MITL formula within negation
    def _naux(
        self, formula: mitl.Mitl, trace_idx: int, formula_idx: int
    ) -> mitl.Interval | None:
        assert formula_idx <= len(self.indices)
        if isinstance(formula, mitl.Prop):
            return None
        if isinstance(formula, mitl.Not):
            return self._aux(formula.operand, trace_idx, formula_idx)
        if isinstance(formula, mitl.And):
            return self._naux_and(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Or):
            return self._naux_or(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Implies):
            return self._naux_implies(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Eventually):
            return self._naux_eventually(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Always):
            return self._naux_always(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Until):
            return self._naux_until(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Release):
            return self._naux_release(formula, trace_idx, formula_idx)
        raise ValueError(f"Unsupported MITL construct: {formula}")

    def weaken(self) -> mitl.Interval | None:
        return self._aux(self.formula, 0, 0)
