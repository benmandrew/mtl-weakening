"""MTL (Metric Temporal Logic) formula AST and transformation operations."""

from dataclasses import dataclass

from src.logic import ltl

Interval = tuple[int, int | None]


class Mtl:
    """Base class for all MTL abstract syntax tree nodes."""

    def __str__(self) -> str:
        """Return the canonical textual form of this MTL formula."""
        return to_string(self)

    def __repr__(self) -> str:
        """Return a concise debug representation for this formula."""
        return to_string(self)


@dataclass(frozen=True, order=True, repr=False)
class TrueBool(Mtl):
    """MTL boolean literal true."""


@dataclass(frozen=True, order=True, repr=False)
class FalseBool(Mtl):
    """MTL boolean literal false."""


@dataclass(frozen=True, order=True, repr=False)
class Prop(Mtl):
    """Atomic proposition node."""

    name: str


@dataclass(frozen=True, order=True, repr=False)
class Not(Mtl):
    """Unary logical negation node."""

    operand: Mtl


@dataclass(frozen=True, order=True, repr=False)
class And(Mtl):
    """Binary logical conjunction node."""

    left: Mtl
    right: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Or(Mtl):
    """Binary logical disjunction node."""

    left: Mtl
    right: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Implies(Mtl):
    """Binary logical implication node."""

    left: Mtl
    right: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Next(Mtl):
    """Next-time temporal operator node."""

    operand: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Eventually(Mtl):
    """Bounded or unbounded eventually temporal operator node."""

    operand: Mtl
    interval: Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class Always(Mtl):
    """Bounded or unbounded always temporal operator node."""

    operand: Mtl
    interval: Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class Until(Mtl):
    """Bounded or unbounded until temporal operator node."""

    left: Mtl
    right: Mtl
    interval: Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class Release(Mtl):
    """Bounded or unbounded release temporal operator node."""

    left: Mtl
    right: Mtl
    interval: Interval = (0, None)


Temporal = Eventually | Always | Until | Release


def _mtl_to_ltl_eventually(formula: Eventually) -> ltl.Ltl:
    """Translate a bounded/unbounded eventually node into equivalent LTL."""
    a, b = formula.interval
    subf = mtl_to_ltl(formula.operand)
    out = subf
    if b is None:
        out = ltl.Eventually(subf)
    else:
        for _ in range(b - a):
            out = ltl.Or(subf, ltl.Next(out))
    for _ in range(a):
        out = ltl.Next(out)
    return out


def _mtl_to_ltl_always(formula: Always) -> ltl.Ltl:
    """Translate a bounded/unbounded always node into equivalent LTL."""
    a, b = formula.interval
    subf = mtl_to_ltl(formula.operand)
    out = subf
    if b is None:
        out = ltl.Always(subf)
    else:
        for _ in range(b - a):
            out = ltl.And(subf, ltl.Next(out))
    for _ in range(a):
        out = ltl.Next(out)
    return out


def _mtl_to_ltl_until(formula: Until) -> ltl.Ltl:
    """Translate a bounded/unbounded until node into equivalent LTL."""
    a, b = formula.interval
    left = mtl_to_ltl(formula.left)
    right = mtl_to_ltl(formula.right)
    if b is None:
        return apply_next_k(ltl.Until(left, right), a)
    terms = []
    for i in range(b - a + 1):
        out = right
        for _ in range(i):
            out = ltl.And(left, ltl.Next(out))
        terms.append(out)
    return apply_next_k(make_disjunction(terms), a)


def _mtl_to_ltl_release(formula: Release) -> ltl.Ltl:
    """Translate a bounded/unbounded release node into equivalent LTL."""
    a, b = formula.interval
    left = mtl_to_ltl(formula.left)
    right = mtl_to_ltl(formula.right)
    if b is None:
        return apply_next_k(ltl.Release(left, right), a)
    out = right
    for _ in range(b - a):
        out = ltl.And(right, ltl.Next(out))
    terms = [out]
    for i in range(b - a + 1):
        out = ltl.And(left, right)
        for _ in range(i):
            out = ltl.And(right, ltl.Next(out))
        terms.append(out)
    return apply_next_k(make_disjunction(terms), a)


def mtl_to_ltl(formula: Mtl) -> ltl.Ltl:
    """Translate an MTL AST into an equivalent LTL AST."""
    if isinstance(formula, TrueBool):
        return ltl.TrueBool()
    if isinstance(formula, FalseBool):
        return ltl.FalseBool()
    if isinstance(formula, Prop):
        return ltl.Prop(formula.name)
    if isinstance(formula, Not):
        return ltl.Not(mtl_to_ltl(formula.operand))
    if isinstance(formula, And):
        return ltl.And(mtl_to_ltl(formula.left), mtl_to_ltl(formula.right))
    if isinstance(formula, Or):
        return ltl.Or(mtl_to_ltl(formula.left), mtl_to_ltl(formula.right))
    if isinstance(formula, Implies):
        return ltl.Implies(mtl_to_ltl(formula.left), mtl_to_ltl(formula.right))
    if isinstance(formula, Eventually):
        return _mtl_to_ltl_eventually(formula)
    if isinstance(formula, Always):
        return _mtl_to_ltl_always(formula)
    if isinstance(formula, Until):
        return _mtl_to_ltl_until(formula)
    if isinstance(formula, Release):
        return _mtl_to_ltl_release(formula)
    if isinstance(formula, Next):
        return ltl.Next(mtl_to_ltl(formula.operand))
    msg = "Unsupported MTL construct"
    raise TypeError(msg)


def apply_next_k(formula: ltl.Ltl, k: int) -> ltl.Ltl:
    """Prefix an LTL formula with k nested next operators."""
    for _ in range(k):
        formula = ltl.Next(formula)
    return formula


def make_disjunction(terms: list[ltl.Ltl]) -> ltl.Ltl:
    """Build a left-associated disjunction from a list of terms."""
    if not terms:
        return ltl.Prop("FALSE")
    result = terms[0]
    for t in terms[1:]:
        result = ltl.Or(result, t)
    return result


class DeBruijnIndexError(IndexError):
    """Raised when a De Bruijn path is invalid for a formula tree."""

    def __init__(
        self,
        indices: list[int],
        formula_idx: int,
        formula: Mtl,
    ) -> None:
        super().__init__(
            f"De Bruijn index {indices} at i={formula_idx} invalid for {formula}",
        )
        self.indices = indices
        self.formula_idx = formula_idx
        self.formula = formula


def fmt_interval(interval: Interval) -> str:
    """Format an interval using the project's textual MTL convention."""
    low, high = interval
    if high is None:
        if low == 0:
            return ""
        return f"[{low}, ∞)"
    return f"[{low}, {high}]"


def to_string(formula: Mtl) -> str:
    """Render an MTL AST as canonical textual syntax."""
    if isinstance(formula, TrueBool):
        return "TRUE"
    if isinstance(formula, FalseBool):
        return "FALSE"
    if isinstance(formula, Prop):
        return formula.name
    if isinstance(formula, Not):
        return f"!({to_string(formula.operand)})"
    if isinstance(formula, And):
        return f"({to_string(formula.left)} & {to_string(formula.right)})"
    if isinstance(formula, Or):
        return f"({to_string(formula.left)} | {to_string(formula.right)})"
    if isinstance(formula, Implies):
        return f"({to_string(formula.left)} -> {to_string(formula.right)})"
    if isinstance(formula, Eventually):
        return (
            f"F{fmt_interval(formula.interval)} ({to_string(formula.operand)})"
        )
    if isinstance(formula, Always):
        return (
            f"G{fmt_interval(formula.interval)} ({to_string(formula.operand)})"
        )
    if isinstance(formula, Until):
        return (
            f"({to_string(formula.left)} "
            f"U{fmt_interval(formula.interval)} "
            f"{to_string(formula.right)})"
        )
    if isinstance(formula, Release):
        return (
            f"({to_string(formula.left)} "
            f"R{fmt_interval(formula.interval)} "
            f"{to_string(formula.right)})"
        )
    if isinstance(formula, Next):
        return f"X ({to_string(formula.operand)})"
    msg = f"Unsupported MTL construct: {formula}"
    raise TypeError(msg)
