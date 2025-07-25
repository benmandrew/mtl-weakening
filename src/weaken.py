from typing import cast

from src import marking
from src.logic import mtl


def get_subformula(formula: mtl.Mtl, indices: list[int]) -> mtl.Mtl:
    for i, idx in enumerate(indices):
        if isinstance(formula, mtl.Prop):
            raise mtl.DeBruijnIndexError(indices, i, formula)
        if isinstance(formula, (mtl.Not, mtl.Eventually, mtl.Always)):
            if idx == 0:
                formula = formula.operand
            else:
                raise mtl.DeBruijnIndexError(indices, i, formula)
        elif isinstance(formula, (mtl.And, mtl.Or, mtl.Implies, mtl.Until)):
            formula, _ = get_de_bruijn_binary(formula, indices, i)
        else:
            raise ValueError(f"Unsupported MTL construct: {formula}")
    return formula


def get_de_bruijn_binary(
    formula: mtl.And | mtl.Or | mtl.Implies | mtl.Until,
    indices: list[int],
    formula_idx: int,
) -> tuple[mtl.Mtl, mtl.Mtl]:
    """
    Return the binary operands of a formula ordered by De Bruijn index.

    Given a binary MTL formula and a list of De Bruijn indices,
    this function returns a tuple of (primary, secondary) operands,
    where the primary operand corresponds to the De Bruijn index at
    the given formula_idx. The secondary is the other operand.

    Raises:
        DeBruijnIndexError: If the index is not 0 or 1.
    """
    if indices[formula_idx] == 0:
        return formula.left, formula.right
    if indices[formula_idx] == 1:
        return formula.right, formula.left
    raise mtl.DeBruijnIndexError(indices, formula_idx, formula)


class Weaken:
    """
    Performs trace-guided interval weakening of MTL subformulas.

    The subformula to weaken is identified by a De Bruijn index.
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
        formula: mtl.Mtl,
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
            self.subformula,
            (mtl.Always, mtl.Eventually, mtl.Until),
        ):
            self.original_interval = self.subformula.interval
        else:
            raise ValueError(f"Cannot weaken MTL subformula: {self.subformula}")

    def interval_abs_diff(
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
        self, formula: mtl.And, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside conjunction.
        """
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if not self.markings.get(secondary, trace_idx):
            return None
        return self._aux(primary, trace_idx, formula_idx + 1)

    def _naux_and(
        self, formula: mtl.And, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside conjunction in negative polarity.
        """
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if self.markings.get(secondary, trace_idx):
            return self.original_interval
        return self._naux(primary, trace_idx, formula_idx + 1)

    def _aux_or(
        self, formula: mtl.Or, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside disjunction.
        """
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if self.markings.get(secondary, trace_idx):
            return self.original_interval
        return self._aux(primary, trace_idx, formula_idx + 1)

    def _naux_or(
        self, formula: mtl.Or, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside disjunction in negative polarity.
        """
        primary, secondary = get_de_bruijn_binary(
            formula, self.indices, formula_idx
        )
        if not self.markings.get(secondary, trace_idx):
            return None
        return self._naux(primary, trace_idx, formula_idx + 1)

    def _aux_implies(
        self, formula: mtl.Implies, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside implication.
        """
        # Don't rewrite as disjunction as it changes the De Bruijn index!
        raise NotImplementedError("")

    def _naux_implies(
        self, formula: mtl.Implies, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside implication implication in negative polarity by .
        """
        # Don't rewrite as disjunction as it changes the De Bruijn index!
        raise NotImplementedError("")

    def _weaken_eventually(
        self, formula: mtl.Eventually, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Directly weaken interval of eventually operator.
        """
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of F[{a}, ∞)")
        # Expand the interval until we find a state when the operand is true
        for i in range(a, self.trace_len * 2):
            if self.markings.get(formula.operand, trace_idx + i):
                return a, max(b, i)
        return None

    def _nweaken_eventually(
        self, formula: mtl.Eventually, trace_idx: int
    ) -> mtl.Interval | None:
        """
        Directly weaken interval of eventually operator in negative polarity.
        """
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        # Expand the interval until we find a state when the operand is false
        for i in range(a, right_idx):
            if not self.markings.get(formula.operand, trace_idx + i):
                if i == a:
                    return None
                return a, i
        return a, b

    def _aux_eventually(
        self, formula: mtl.Eventually, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside eventually operator.
        """
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

    def _naux_eventually(
        self, formula: mtl.Eventually, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside eventually operator in negative polarity.
        """
        if formula_idx == len(self.indices):
            return self._nweaken_eventually(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        intervals = []
        for i in range(a, right_idx):
            interval = self._naux(
                formula.operand, trace_idx + i, formula_idx + 1
            )
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=self.interval_abs_diff)

    def _weaken_always(self, formula: mtl.Always, trace_idx: int):
        """
        Directly weaken interval of always operator.
        """
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        # Expand the interval until we find a state when the operand is false,
        # then reduce the interval to just before that
        for i in range(a, right_idx):
            if not self.markings.get(formula.operand, trace_idx + i):
                if i == a:
                    return None
                return a, i - 1
        return a, b

    def _nweaken_always(self, formula: mtl.Always, trace_idx: int):
        """
        Directly weaken interval of always operator in negative polarity.
        """
        a, b = formula.interval
        if b is None:
            raise ValueError(
                f"Cannot weaken interval of G[{a}, ∞) in negative polarity"
            )
        # Expand the interval until we find a state when the operand is true,
        # then reduce the interval to just before that
        for i in range(a, self.trace_len * 2):
            if not self.markings.get(formula.operand, trace_idx + i):
                return a, max(b, i)
        return None

    def _aux_always(
        self, formula: mtl.Always, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside always operator.
        """
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

    def _naux_always(
        self, formula: mtl.Always, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside always operator in negative polarity.
        """
        if formula_idx == len(self.indices):
            return self._nweaken_always(formula, trace_idx)
        a, b = formula.interval
        right_idx = self.trace_len if b is None else b + 1
        all_intervals = [
            self._naux(formula.operand, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=self.interval_abs_diff)

    def _weaken_until(self, formula: mtl.Until, trace_idx: int):
        """
        Directly weaken interval of until operator.
        """
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of U[{a}, ∞)")
        for i in range(a, self.trace_len * 2):
            if self.markings.get(formula.right, trace_idx + i):
                return a, max(b, i)
            if not self.markings.get(formula.left, trace_idx + i):
                break
        return None

    def _nweaken_until(self, formula: mtl.Until, trace_idx: int):
        """
        Directly weaken interval of until operator in negative polarity.
        """
        raise NotImplementedError("")

    def _aux_until_left(
        self, formula: mtl.Until, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside until operator on the left side.
        """
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

    def _naux_until_left(
        self, formula: mtl.Until, trace_idx: int, formula_idx: int
    ):
        """
        Weakening inside until operator on the left side in negative polarity.
        """
        raise NotImplementedError("")

    def _aux_until_right(
        self, formula: mtl.Until, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Weakening inside until operator on the right side."""
        a, b = formula.interval
        right_idx = self.trace_len * 2 if b is None else b + 1
        valid_intervals: list[mtl.Interval | None] = []
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

    def _naux_until_right(
        self, formula: mtl.Until, trace_idx: int, formula_idx: int
    ):
        """
        Weakening inside until operator on the right side in negative polarity.
        """
        raise NotImplementedError("")

    def _aux_until(
        self, formula: mtl.Until, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Recursively weakens until operator subformulas.
        """
        if formula_idx == len(self.indices):
            return self._weaken_until(formula, trace_idx)
        if self.indices[formula_idx] == 0:
            return self._aux_until_left(formula, trace_idx, formula_idx)
        if self.indices[formula_idx] == 1:
            return self._aux_until_right(formula, trace_idx, formula_idx)
        raise mtl.DeBruijnIndexError(self.indices, formula_idx, formula)

    def _naux_until(
        self, formula: mtl.Until, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Recursively weakens until operator subformulas in negative polarity.
        """
        if formula_idx == len(self.indices):
            return self._nweaken_until(formula, trace_idx)
        if self.indices[formula_idx] == 0:
            return self._naux_until_left(formula, trace_idx, formula_idx)
        if self.indices[formula_idx] == 1:
            return self._naux_until_right(formula, trace_idx, formula_idx)
        raise mtl.DeBruijnIndexError(self.indices, formula_idx, formula)

    def _aux(
        self, formula: mtl.Mtl, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Recursively weakens subformulas in positive polarity.

        Follows the De Bruijn index to the target subformula. If the
        index matches, the corresponding `_weaken_*` method is applied.

        Otherwise, recursion proceeds through `_aux_*` operator-specific
        handlers. Negations flip polarity and delegate to `_naux`.
        """
        assert formula_idx <= len(self.indices)
        if isinstance(formula, mtl.Prop):
            return None
        if isinstance(formula, mtl.Not):
            return self._naux(formula.operand, trace_idx, formula_idx + 1)
        if isinstance(formula, mtl.And):
            return self._aux_and(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Or):
            return self._aux_or(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Implies):
            return self._aux_implies(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Eventually):
            return self._aux_eventually(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Always):
            return self._aux_always(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Until):
            return self._aux_until(formula, trace_idx, formula_idx)
        raise ValueError(f"Unsupported MTL construct: {formula}")

    def _naux(
        self, formula: mtl.Mtl, trace_idx: int, formula_idx: int
    ) -> mtl.Interval | None:
        """
        Recursively weakens subformulas in negative polarity.

        Operates under negation, treating each operator via `_naux_*`
        methods. A nested negation flips polarity back to `_aux`.

        This structure mirrors the NNF of the formula and ensures
        dual-handling of temporal and boolean constructs.
        """
        assert formula_idx <= len(self.indices)
        if isinstance(formula, mtl.Prop):
            return None
        if isinstance(formula, mtl.Not):
            return self._aux(formula.operand, trace_idx, formula_idx + 1)
        if isinstance(formula, mtl.And):
            return self._naux_and(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Or):
            return self._naux_or(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Implies):
            return self._naux_implies(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Eventually):
            return self._naux_eventually(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Always):
            return self._naux_always(formula, trace_idx, formula_idx)
        if isinstance(formula, mtl.Until):
            return self._naux_until(formula, trace_idx, formula_idx)
        raise ValueError(f"Unsupported MTL construct: {formula}")

    def weaken(self) -> mtl.Interval | None:
        """
        Do weakening.
        """
        return self._aux(self.formula, 0, 0)
