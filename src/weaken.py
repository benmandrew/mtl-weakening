from typing import Optional
import functools
from src import mitl
from src import marking


def get_subformula(formula: mitl.Mitl, indices: list[int]) -> mitl.Mitl:
    for i in indices:
        if isinstance(formula, mitl.Prop):
            IndexError(
                f"De Bruijn index {i} invalid for {mitl.to_string(formula)}"
            )
        if (
            isinstance(formula, mitl.Not)
            or isinstance(formula, mitl.Eventually)
            or isinstance(formula, mitl.Always)
        ):
            if i == 0:
                formula = formula.operand
            else:
                IndexError(
                    f"De Bruijn index {i} invalid for {mitl.to_string(formula)}"
                )
        elif (
            isinstance(formula, mitl.And)
            or isinstance(formula, mitl.Or)
            or isinstance(formula, mitl.Implies)
            or isinstance(formula, mitl.Until)
        ):
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
    if isinstance(subformula, mitl.Always):
        interval_comparator = max_interval
    elif isinstance(subformula, mitl.Eventually):
        interval_comparator = min_interval
    else:
        raise ValueError(f"Unsupported MITL construct: {subformula}")

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
        intervals = [
            aux(formula.operand, trace_idx + i, formula_idx + 1)
            for i in range(a, right_idx)
        ]
        print("  " * formula_idx + "Eventually", intervals)
        # return functools.reduce(max_interval, intervals)
        return functools.reduce(interval_comparator, intervals)

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
        # return functools.reduce(max_interval, intervals, None)
        return functools.reduce(interval_comparator, intervals, None)

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
