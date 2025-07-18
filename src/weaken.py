from typing import Optional

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


def max_interval(
    interval_a: Optional[tuple[int, int]],
    interval_b: Optional[tuple[int, int]],
) -> Optional[tuple[int, int]]:
    if interval_a is None and interval_b is None:
        return None
    if interval_a is None:
        return interval_b
    if interval_b is None:
        return interval_a
    if interval_a[0] <= interval_b[0] and interval_a[1] >= interval_b[1]:
        return interval_a
    if interval_a[0] >= interval_b[0] and interval_a[1] <= interval_b[1]:
        return interval_b
    raise ValueError("Non-overlapping intervals")


def min_interval(
    interval_a: Optional[tuple[int, int]],
    interval_b: Optional[tuple[int, int]],
) -> Optional[tuple[int, int]]:
    if interval_a is None and interval_b is None:
        return None
    if interval_a is None:
        return interval_b
    if interval_b is None:
        return interval_a
    if interval_a[0] >= interval_b[0] and interval_a[1] <= interval_b[1]:
        return interval_a
    if interval_a[0] <= interval_b[0] and interval_a[1] >= interval_b[1]:
        return interval_b
    raise ValueError("Non-overlapping intervals")


def weaken_interval(
    formula: mitl.Mitl,
    indices: list[int],
    trace: marking.Trace,
    markings: marking.Marking,
):
    trace_len = len(trace)
    subformula = get_subformula(formula, indices)
    if isinstance(subformula, (mitl.Always, mitl.Eventually)):
        target_interval = subformula.interval
    else:
        raise ValueError(f"Cannot weaken MITL subformula: {subformula}")

    def interval_abs_diff(
        interval: tuple[int, int],
    ) -> int:
        second = (
            abs(interval[1])
            if target_interval[1] is None
            else abs(interval[1] - target_interval[1])
        )
        return abs(interval[0] - target_interval[0]) + second

    def aux_and(
        formula: mitl.And, trace_idx: int, formula_idx: int
    ) -> Optional[tuple[int, int]]:
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
    ) -> Optional[tuple[int, int]]:
        raise NotImplementedError("")

    def aux_implies(
        formula: mitl.Implies, trace_idx: int, formula_idx: int
    ) -> Optional[tuple[int, int]]:
        raise NotImplementedError("")

    def weaken_eventually(
        formula: mitl.Eventually, trace_idx: int
    ) -> Optional[tuple[int, int]]:
        a, b = formula.interval
        if b is None:
            raise ValueError(f"Cannot weaken interval of F[{a}, ∞)")
        for i in range(a, trace_len):
            if markings[formula.operand][trace.idx(trace_idx + i)]:
                return a, max(b, i)
        return None

    def aux_eventually(
        formula: mitl.Eventually, trace_idx: int, formula_idx: int
    ) -> Optional[tuple[int, int]]:
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
        print("  " * formula_idx + "Eventually", all_intervals)
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
    ) -> Optional[tuple[int, int]]:
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
        print("  " * formula_idx + "Always", intervals)
        return max(intervals, key=interval_abs_diff)

    def aux_until(
        formula: mitl.Until, trace_idx: int, formula_idx: int
    ) -> Optional[tuple[int, int]]:
        raise NotImplementedError("")

    def aux(
        formula: mitl.Mitl, trace_idx: int, formula_idx: int
    ) -> Optional[tuple[int, int]]:
        assert formula_idx <= len(indices)
        if isinstance(formula, mitl.Prop):
            return None
        if isinstance(formula, mitl.Not):
            raise ValueError("Not not supported")
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
