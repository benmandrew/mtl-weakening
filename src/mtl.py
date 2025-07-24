from dataclasses import dataclass

from src import ltl

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


@dataclass(frozen=True, order=True, repr=False)
class Release(Mtl):
    left: Mtl
    right: Mtl
    interval: Interval = (0, None)


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
    if isinstance(formula, Always):
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
    if isinstance(formula, Until):
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
    if isinstance(formula, Release):
        rewrite = Not(
            Until(Not(formula.left), Not(formula.right), formula.interval)
        )
        return mtl_to_ltl(rewrite)
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


def get_de_bruijn(
    formula: Mtl,
    indices: list[int],
    formula_idx: int,
) -> Mtl:
    if (
        isinstance(formula, (Not, Eventually, Always, Next))
        and indices[formula_idx] == 0
    ):
        return formula.operand
    if isinstance(formula, (And, Or, Implies, Until, Release)):
        if indices[formula_idx] == 0:
            return formula.left
        if indices[formula_idx] == 1:
            return formula.right
    raise DeBruijnIndexError(indices, formula_idx, formula)


def to_nnf_in_not(formula: Mtl) -> Mtl:
    if isinstance(formula, Prop):
        return Not(formula)
    if isinstance(formula, Not):
        return to_nnf(formula.operand)
    if isinstance(formula, And):
        return Or(to_nnf(Not(formula.left)), to_nnf(Not(formula.right)))
    if isinstance(formula, Or):
        return And(to_nnf(Not(formula.left)), to_nnf(Not(formula.right)))
    if isinstance(formula, Implies):
        return And(to_nnf(formula.left), to_nnf(Not(formula.right)))
    if isinstance(formula, Eventually):
        return Always(to_nnf(Not(formula.operand)), formula.interval)
    if isinstance(formula, Always):
        return Eventually(to_nnf(Not(formula.operand)), formula.interval)
    if isinstance(formula, Until):
        return Release(
            to_nnf(Not(formula.left)),
            to_nnf(Not(formula.right)),
            formula.interval,
        )
    if isinstance(formula, Release):
        return Until(
            to_nnf(Not(formula.left)),
            to_nnf(Not(formula.right)),
            formula.interval,
        )
    if isinstance(formula, Next):
        return Next(to_nnf(Not(formula.operand)))
    raise ValueError(f"Unexpected formula in Not: {formula}")


def to_nnf(formula: Mtl) -> Mtl:
    if isinstance(formula, Prop):
        return formula
    if isinstance(formula, Not):
        return to_nnf_in_not(formula.operand)
    if isinstance(formula, And):
        return And(to_nnf(formula.left), to_nnf(formula.right))
    if isinstance(formula, Or):
        return Or(to_nnf(formula.left), to_nnf(formula.right))
    if isinstance(formula, Implies):
        return Or(to_nnf(Not(formula.left)), to_nnf(formula.right))
    if isinstance(formula, Eventually):
        return Eventually(to_nnf(formula.operand), formula.interval)
    if isinstance(formula, Always):
        return Always(to_nnf(formula.operand), formula.interval)
    if isinstance(formula, Until):
        return Until(
            to_nnf(formula.left), to_nnf(formula.right), formula.interval
        )
    if isinstance(formula, Release):
        return Release(
            to_nnf(formula.left), to_nnf(formula.right), formula.interval
        )
    if isinstance(formula, Next):
        return Next(to_nnf(formula.operand))
    raise ValueError(f"Unknown MTL formula type: {type(formula)}")


# def _convert_indices_to_nnf_not_aux(
#     formula: Mtl, indices: list[int], formula_idx: int
# ) -> list[int]:
#     if isinstance(formula, Prop):
#         return indices
#     if isinstance(formula, Not):
#         del indices[formula_idx - 1 : formula_idx + 1]
#         return _convert_indices_to_nnf_aux(
#             formula.operand, indices, formula_idx - 1
#         )
#     if isinstance(formula, (And, Or)):
#         primary = get_de_bruijn(formula, indices, formula_idx)
#         del indices[formula_idx]
#         indices.insert(formula_idx + 1, 0)
#         return _convert_indices_to_nnf_aux(primary, indices, formula_idx + 2)
#     if isinstance(formula, Implies):
#         del indices[formula_idx]
#         if indices[formula_idx] == 0:
#             return _convert_indices_to_nnf_aux(
#                 formula.left, indices, formula_idx + 1
#             )
#         if indices[formula_idx] == 1:
#             indices.insert(formula_idx + 1, 0)
#             return _convert_indices_to_nnf_aux(
#                 formula.right, indices, formula_idx + 2
#             )
#         raise IndexError(
#             f"De Bruijn index {indices} at i={formula_idx} invalid for {formula}"
#         )
#     if isinstance(formula, Eventually):
#         return Always(to_nnf(Not(formula.operand)), formula.interval)
#     if isinstance(formula, Always):
#         return Eventually(to_nnf(Not(formula.operand)), formula.interval)
#     if isinstance(formula, Until):
#         return Release(
#             to_nnf(Not(formula.left)),
#             to_nnf(Not(formula.right)),
#             formula.interval,
#         )
#     if isinstance(formula, Release):
#         return Until(
#             to_nnf(Not(formula.left)),
#             to_nnf(Not(formula.right)),
#             formula.interval,
#         )
#     if isinstance(formula, Next):
#         return Next(to_nnf(Not(formula.operand)))
#     raise ValueError(f"Unexpected formula in Not: {formula}")


# def _convert_indices_to_nnf_aux(
#     formula: Mtl, indices: list[int], formula_idx: int
# ) -> list[int]:
#     if isinstance(formula, Prop):
#         return indices
#     if isinstance(formula, Not):
#         return _convert_indices_to_nnf_not_aux(
#             formula.operand, indices, formula_idx + 1
#         )
#     if isinstance(formula, And):
#         return And(to_nnf(formula.left), to_nnf(formula.right))
#     if isinstance(formula, Or):
#         return Or(to_nnf(formula.left), to_nnf(formula.right))
#     if isinstance(formula, Implies):
#         return Or(to_nnf(Not(formula.left)), to_nnf(formula.right))
#     if isinstance(formula, Eventually):
#         return Eventually(to_nnf(formula.operand), formula.interval)
#     if isinstance(formula, Always):
#         return Always(to_nnf(formula.operand), formula.interval)
#     if isinstance(formula, Until):
#         return Until(
#             to_nnf(formula.left), to_nnf(formula.right), formula.interval
#         )
#     if isinstance(formula, Release):
#         return Release(
#             to_nnf(formula.left), to_nnf(formula.right), formula.interval
#         )
#     if isinstance(formula, Next):
#         return Next(to_nnf(formula.operand))
#     raise ValueError(f"Unknown MTL formula type: {type(formula)}")


# # Convert De Bruijn indices of a formula to that of the NNF version.
# def convert_indices_to_nnf(formula: Mtl, indices: list[int]) -> list[int]:
#     return _convert_indices_to_nnf_aux(formula, indices, 0)


def to_string(formula: Mtl) -> str:
    def fmt_interval(interval: Interval) -> str:
        low, high = interval
        if high is None:
            if low == 0:
                return ""
            return f"[{low}, ∞)"
        return f"[{low}, {high}]"

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
        elif isinstance(f, (And, Or, Implies, Until, Release)):
            aux(f.left)
            aux(f.right)
        else:
            raise ValueError(f"Unsupported MTL construct: {f}")
        return label

    aux(f)
    return "\n".join(ltlspec_lines), subformulae
