from dataclasses import dataclass

from src.logic import ltl

Interval = tuple[int, int | None]


class Mtl:
    def __str__(self) -> str:
        return to_string(self)

    def __repr__(self) -> str:
        return to_string(self)


@dataclass(frozen=True, order=True, repr=False)
class Prop(Mtl):
    name: str


@dataclass(frozen=True, order=True, repr=False)
class Not(Mtl):
    operand: Mtl


@dataclass(frozen=True, order=True, repr=False)
class And(Mtl):
    left: Mtl
    right: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Or(Mtl):
    left: Mtl
    right: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Implies(Mtl):
    left: Mtl
    right: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Next(Mtl):
    operand: Mtl


@dataclass(frozen=True, order=True, repr=False)
class Eventually(Mtl):
    operand: Mtl
    interval: Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class Always(Mtl):
    operand: Mtl
    interval: Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class Until(Mtl):
    left: Mtl
    right: Mtl
    interval: Interval = (0, None)


def _mtl_to_ltl_eventually(formula: Eventually) -> ltl.Ltl:
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


def mtl_to_ltl(formula: Mtl) -> ltl.Ltl:
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
    raise ValueError("Unsupported MTL construct")


def apply_next_k(formula: ltl.Ltl, k: int) -> ltl.Ltl:
    for _ in range(k):
        formula = ltl.Next(formula)
    return formula


def make_conjunction(terms: list[ltl.Ltl]) -> ltl.Ltl:
    if not terms:
        return ltl.Prop("TRUE")
    result = terms[0]
    for t in terms[1:]:
        result = ltl.And(result, t)
    return result


def make_disjunction(terms: list[ltl.Ltl]) -> ltl.Ltl:
    if not terms:
        return ltl.Prop("FALSE")
    result = terms[0]
    for t in terms[1:]:
        result = ltl.Or(result, t)
    return result


class DeBruijnIndexError(IndexError):
    def __init__(self, indices: list[int], formula_idx: int, formula: Mtl):
        super().__init__(
            f"De Bruijn index {indices} at i={formula_idx} invalid for {formula}"
        )
        self.indices = indices
        self.formula_idx = formula_idx
        self.formula = formula


def fmt_interval(interval: Interval) -> str:
    low, high = interval
    if high is None:
        if low == 0:
            return ""
        return f"[{low}, ∞)"
    return f"[{low}, {high}]"


def to_string(formula: Mtl) -> str:

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
    if isinstance(formula, Next):
        return f"X ({to_string(formula.operand)})"
    raise ValueError(f"Unsupported MTL construct: {formula}")


def generate_subformulae_smv(f: Mtl, num_states: int) -> tuple[str, list[Mtl]]:
    label_map: dict[Mtl, str] = {}
    ltlspec_lines = []
    subformulae = []
    counter = 1

    def get_label():
        nonlocal counter
        label = f"f{counter}"
        counter += 1
        return label

    def aux(f: Mtl):
        subformulae.append(f)
        for i in range(num_states):
            g = Always(Implies(Prop(f"state = {i}"), f))
            if g in label_map:
                return label_map[g]
            label = get_label()
            expr = ltl.to_nuxmv(mtl_to_ltl(g))
            label_map[g] = label
            ltlspec_lines.append(f"LTLSPEC NAME {label} := {expr};")
        if isinstance(f, Prop):
            pass
        elif isinstance(f, (Not, Eventually, Always)):
            aux(f.operand)
        elif isinstance(f, (And, Or, Implies, Until)):
            aux(f.left)
            aux(f.right)
        else:
            raise ValueError(f"Unsupported MTL construct: {f}")
        return label

    aux(f)
    return "\n".join(ltlspec_lines), subformulae
