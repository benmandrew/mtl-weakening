from dataclasses import dataclass
from typing import Optional

from src import ltl

Interval = tuple[int, Optional[int]]


class Mitl:
    pass


@dataclass(frozen=True, order=True)
class Prop(Mitl):
    name: str


@dataclass(frozen=True, order=True)
class Not(Mitl):
    operand: Mitl


@dataclass(frozen=True, order=True)
class And(Mitl):
    left: Mitl
    right: Mitl


@dataclass(frozen=True, order=True)
class Or(Mitl):
    left: Mitl
    right: Mitl


@dataclass(frozen=True, order=True)
class Implies(Mitl):
    left: Mitl
    right: Mitl


@dataclass(frozen=True, order=True)
class Next(Mitl):
    operand: Mitl


@dataclass(frozen=True, order=True)
class Eventually(Mitl):
    operand: Mitl
    interval: Interval = (0, None)


@dataclass(frozen=True, order=True)
class Always(Mitl):
    operand: Mitl
    interval: Interval = (0, None)


@dataclass(frozen=True, order=True)
class Until(Mitl):
    left: Mitl
    right: Mitl
    interval: Interval = (0, None)


def mitl_to_ltl(formula: Mitl) -> ltl.Ltl:
    if isinstance(formula, Prop):
        return ltl.Prop(formula.name)
    if isinstance(formula, Not):
        return ltl.Not(mitl_to_ltl(formula.operand))
    if isinstance(formula, And):
        return ltl.And(mitl_to_ltl(formula.left), mitl_to_ltl(formula.right))
    if isinstance(formula, Or):
        return ltl.Or(mitl_to_ltl(formula.left), mitl_to_ltl(formula.right))
    if isinstance(formula, Implies):
        return ltl.Implies(
            mitl_to_ltl(formula.left), mitl_to_ltl(formula.right)
        )
    if isinstance(formula, Eventually):
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
    if isinstance(formula, Always):
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
    if isinstance(formula, Until):
        a, b = formula.interval
        left = mitl_to_ltl(formula.left)
        right = mitl_to_ltl(formula.right)
        if b is None:
            return apply_next_k(ltl.Until(left, right), a)
        terms = []
        for i in range(b - a + 1):
            out = right
            for _ in range(i):
                out = ltl.And(left, ltl.Next(out))
            terms.append(out)
        return apply_next_k(make_disjunction(terms), a)
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
        elif isinstance(f, (And, Or, Implies)):
            aux(f.left)
            aux(f.right)
        elif isinstance(f, (Eventually, Always)):
            aux(f.operand)
        elif isinstance(f, Until):
            aux(f.left)
            aux(f.right)
        else:
            raise ValueError(f"Unsupported MITL construct: {f}")
        return label

    aux(f)
    return "\n".join(ltlspec_lines), subformulae
