from dataclasses import dataclass
from typing import Optional, Tuple
from src import ltl
from src.matchable import matchable


class Mitl:
    pass


@matchable
@dataclass(frozen=True, order=True)
class Prop(Mitl):
    name: str


@matchable
@dataclass(frozen=True, order=True)
class Not(Mitl):
    operand: Mitl


@matchable
@dataclass(frozen=True, order=True)
class And(Mitl):
    left: Mitl
    right: Mitl


@matchable
@dataclass(frozen=True, order=True)
class Or(Mitl):
    left: Mitl
    right: Mitl


@matchable
@dataclass(frozen=True, order=True)
class Implies(Mitl):
    left: Mitl
    right: Mitl


@matchable
@dataclass(frozen=True, order=True)
class Next(Mitl):
    operand: Mitl


@matchable
@dataclass(frozen=True, order=True)
class Eventually(Mitl):
    operand: Mitl
    interval: Tuple[int, Optional[int]] = (0, None)


@matchable
@dataclass(frozen=True, order=True)
class Always(Mitl):
    operand: Mitl
    interval: Tuple[int, Optional[int]] = (0, None)


@matchable
@dataclass(frozen=True, order=True)
class Until(Mitl):
    left: Mitl
    right: Mitl
    interval: Tuple[int, Optional[int]] = (0, None)


def mitl_to_ltl(formula: Mitl) -> ltl.Ltl:
    if isinstance(formula, Prop):
        return ltl.Prop(formula.name)
    elif isinstance(formula, Not):
        return ltl.Not(mitl_to_ltl(formula.operand))
    elif isinstance(formula, And):
        return ltl.And(mitl_to_ltl(formula.left), mitl_to_ltl(formula.right))
    elif isinstance(formula, Or):
        return ltl.Or(mitl_to_ltl(formula.left), mitl_to_ltl(formula.right))
    elif isinstance(formula, Implies):
        return ltl.Implies(
            mitl_to_ltl(formula.left), mitl_to_ltl(formula.right)
        )
    elif isinstance(formula, Eventually):
        a, b = formula.interval
        subf = mitl_to_ltl(formula.operand)
        out = subf
        if b is None:
            out = ltl.Eventually(subf)
        else:
            for _ in range(b - a):
                out = ltl.Or(subf, ltl.Next(out))
        for _ in range(a):
            out = ltl.Next(out)
        return out
    elif isinstance(formula, Always):
        a, b = formula.interval
        subf = mitl_to_ltl(formula.operand)
        out = subf
        if b is None:
            out = ltl.Always(subf)
        else:
            for _ in range(b - a):
                out = ltl.And(subf, ltl.Next(out))
        for _ in range(a):
            out = ltl.Next(out)
        return out
    elif isinstance(formula, Until):
        a, b = formula.interval
        left = mitl_to_ltl(formula.left)
        right = mitl_to_ltl(formula.right)
        if b is None:
            return apply_next_k(ltl.Until(left, right), a)
        else:
            terms = []
            for i in range(b - a + 1):
                out = right
                for _ in range(i):
                    out = ltl.And(left, ltl.Next(out))
                terms.append(out)
            return apply_next_k(make_disjunction(terms), a)
    else:
        raise ValueError("Unsupported MITL construct")


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


def to_string(formula: Mitl) -> str:
    def fmt_interval(interval: Tuple[int, Optional[int]]) -> str:
        low, high = interval
        if high is None:
            return f"[{low}, ∞)"
        return f"[{low}, {high}]"

    if isinstance(formula, Prop):
        return formula.name
    elif isinstance(formula, Not):
        return f"!({to_string(formula.operand)})"
    elif isinstance(formula, And):
        return f"({to_string(formula.left)} & {to_string(formula.right)})"
    elif isinstance(formula, Or):
        return f"({to_string(formula.left)} | {to_string(formula.right)})"
    elif isinstance(formula, Implies):
        return f"({to_string(formula.left)} -> {to_string(formula.right)})"
    elif isinstance(formula, Eventually):
        return (
            f"F{fmt_interval(formula.interval)} ({to_string(formula.operand)})"
        )
    elif isinstance(formula, Always):
        return (
            f"G{fmt_interval(formula.interval)} ({to_string(formula.operand)})"
        )
    elif isinstance(formula, Until):
        return f"({to_string(formula.left)} U{fmt_interval(formula.interval)} {to_string(formula.right)})"
    else:
        raise ValueError(f"Unsupported MITL construct: {formula}")


def generate_subformulae_smv(
    f: Mitl, num_states: int
) -> tuple[str, list[Mitl]]:
    label_map: dict[Mitl, str] = {}
    ltlspec_lines = []
    subformulae = []
    counter = 1

    def get_label():
        nonlocal counter
        label = f"f{counter}"
        counter += 1
        return label

    def aux(f: Mitl):
        subformulae.append(f)
        for i in range(num_states):
            g = Always(Implies(Prop(f"state = {i}"), f))
            if g in label_map:
                return label_map[g]
            label = get_label()
            expr = ltl.to_nuxmv(mitl_to_ltl(g))
            label_map[g] = label
            ltlspec_lines.append(f"LTLSPEC NAME {label} := {expr};")
        if isinstance(f, Prop):
            pass
        elif isinstance(f, Not):
            aux(f.operand)
        elif isinstance(f, And):
            aux(f.left)
            aux(f.right)
        elif isinstance(f, Or):
            aux(f.left)
            aux(f.right)
        elif isinstance(f, Implies):
            aux(f.left)
            aux(f.right)
        elif isinstance(f, Eventually):
            aux(f.operand)
        elif isinstance(f, Always):
            aux(f.operand)
        elif isinstance(f, Until):
            aux(f.left)
            aux(f.right)
        else:
            raise ValueError(f"Unsupported MITL construct: {f}")
        return label

    aux(f)
    return "\n".join(ltlspec_lines), subformulae
