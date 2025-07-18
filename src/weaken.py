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


def weaken_interval(
    formula: mitl.Mitl,
    indices: list[int],
    trace: marking.Trace,
    markings: marking.Marking,
):
    trace_len = len(trace)
    subformula = get_subformula(formula, indices)
    if isinstance(subformula, (mitl.Always, mitl.Eventually)):
        original_interval = subformula.interval
    else:
        raise ValueError(f"Cannot weaken MITL subformula: {subformula}")

    def interval_abs_diff(
        interval: mitl.Interval,
    ) -> int:
        if original_interval[1] is None and interval[1] is None:
            right = 0
        elif original_interval[1] is None:
            right = -cast(int, interval[1])
        else:
            right = abs(
                cast(int, interval[1]) - cast(int, original_interval[1])
            )
        return abs(interval[0] - original_interval[0]) + right

    def aux_not(
        formula: mitl.Not, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        raise NotImplementedError("")

    def aux_and(
        formula: mitl.And, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if indices[formula_idx] == 0:
            if not markings.markings[formula.right][trace_idx]:
                return None
            return aux(formula.left, trace_idx, formula_idx + 1)
        if indices[formula_idx] == 1:
            if not markings.markings[formula.left][trace_idx]:
                return None
            return aux(formula.right, trace_idx, formula_idx + 1)
        raise IndexError(
            f"De Bruijn index {formula_idx} invalid for {mitl.to_string(formula)}"
        )

    def aux_or(
        formula: mitl.Or, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if indices[formula_idx] == 0:
            if markings.markings[formula.right][trace_idx]:
                return original_interval
            return aux(formula.left, trace_idx, formula_idx + 1)
        if indices[formula_idx] == 1:
            if markings.markings[formula.left][trace_idx]:
                return original_interval
            return aux(formula.right, trace_idx, formula_idx + 1)
        raise IndexError(
            f"De Bruijn index {formula_idx} invalid for {mitl.to_string(formula)}"
        )

    def aux_implies(
        formula: mitl.Implies, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        raise NotImplementedError("")

    def weaken_eventually(
        formula: mitl.Eventually, trace_idx: int
    ) -> Optional[mitl.Interval]:
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of F[{a}, ∞)")
        for i in range(a, trace_len):
            if markings[formula.operand][trace.idx(trace_idx + i)]:
                return a, max(b, i)
        return None

    def aux_eventually(
        formula: mitl.Eventually, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if formula_idx == len(indices):
            return weaken_eventually(formula, trace_idx)
        a, b = formula.interval
        right_idx = trace_len if b is None else b + 1
        all_intervals = [
            aux(formula.operand, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        intervals = [i for i in all_intervals if i is not None]
        if intervals == []:
            return None
        return min(intervals, key=interval_abs_diff)

    def weaken_always(formula: mitl.Always, trace_idx: int):
        a, b = formula.interval
        right_idx = trace_len if b is None else b + 1
        # Expand the interval until we find a state when the operand is false,
        # then reduce the interval to just before that
        for i in range(a, right_idx):
            if not markings[formula.operand][trace.idx(trace_idx + i)]:
                if i == a:
                    return None
                return a, i - 1
        return a, b

    def aux_always(
        formula: mitl.Always, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        if formula_idx == len(indices):
            return weaken_always(formula, trace_idx)
        a, b = formula.interval
        right_idx = trace_len if b is None else b + 1
        intervals = []
        for i in range(a, right_idx):
            interval = aux(formula.operand, trace_idx + i, formula_idx + 1)
            if interval is None:
                return None
            intervals.append(interval)
        return max(intervals, key=interval_abs_diff)

    def aux_until(
        formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        raise NotImplementedError("")

    def aux(
        formula: mitl.Mitl, trace_idx: int, formula_idx: int
    ) -> Optional[mitl.Interval]:
        assert formula_idx <= len(indices)
        if isinstance(formula, mitl.Prop):
            return None
        if isinstance(formula, mitl.Not):
            return aux_not(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.And):
            return aux_and(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Or):
            return aux_or(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Implies):
            return aux_implies(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Eventually):
            return aux_eventually(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Always):
            return aux_always(formula, trace_idx, formula_idx)
        if isinstance(formula, mitl.Until):
            return aux_until(formula, trace_idx, formula_idx)
        raise ValueError(f"Unsupported MITL construct: {formula}")

    return aux(formula, 0, 0)
