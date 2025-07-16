from dataclasses import dataclass
from typing import Optional, Tuple
import ltl


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
    interval: Tuple[int, Optional[int]] = (0, None)


@dataclass(frozen=True, order=True)
class Always(Mitl):
    operand: Mitl
    interval: Tuple[int, Optional[int]] = (0, None)


@dataclass(frozen=True, order=True)
class Until(Mitl):
    left: Mitl
    right: Mitl
    interval: Tuple[int, Optional[int]] = (0, None)


def mitl_to_ltl(formula: Mitl) -> ltl.Ltl:
    match formula:
        case Prop(name):
            return ltl.Prop(name)
        case Not(f):
            return ltl.Not(mitl_to_ltl(f))
        case And(l, r):
            return ltl.And(mitl_to_ltl(l), mitl_to_ltl(r))
        case Or(l, r):
            return ltl.Or(mitl_to_ltl(l), mitl_to_ltl(r))
        case Implies(l, r):
            return ltl.Implies(mitl_to_ltl(l), mitl_to_ltl(r))
        case Eventually(f, (a, b)):
            subf = mitl_to_ltl(f)
            out = subf
            if b is None:
                out = ltl.Eventually(subf)
            else:
                for _ in range(b - a):
                    out = ltl.Or(subf, ltl.Next(out))
            for _ in range(a):
                out = ltl.Next(out)
            return out
        case Always(f, (a, b)):
            subf = mitl_to_ltl(f)
            out = subf
            if b is None:
                out = ltl.Always(subf)
            else:
                for _ in range(b - a):
                    out = ltl.And(subf, ltl.Next(out))
            for _ in range(a):
                out = ltl.Next(out)
            return out
        case Until(l, r, (a, b)):
            left = mitl_to_ltl(l)
            right = mitl_to_ltl(r)
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
        case _:
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

    match formula:
        case Prop(name):
            return name
        case Not(f):
            return f"!({to_string(f)})"
        case And(left, right):
            return f"({to_string(left)} & {to_string(right)})"
        case Or(left, right):
            return f"({to_string(left)} | {to_string(right)})"
        case Implies(left, right):
            return f"({to_string(left)} -> {to_string(right)})"
        case Eventually(f, interval):
            return f"F{fmt_interval(interval)} ({to_string(f)})"
        case Always(f, interval):
            return f"G{fmt_interval(interval)} ({to_string(f)})"
        case Until(left, right, interval):
            return f"({to_string(left)} U{fmt_interval(interval)} {to_string(right)})"
        case _:
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

    def aux(f):
        subformulae.append(f)
        for i in range(num_states):
            g = Always(Implies(Prop(f"state = {i}"), f))
            if g in label_map:
                return label_map[g]
            label = get_label()
            expr = ltl.to_nuxmv(mitl_to_ltl(g))
            label_map[g] = label
            ltlspec_lines.append(f"LTLSPEC NAME {label} := {expr};")
        match f:
            case Prop(_):
                pass
            case Not(g):
                aux(g)
            case And(left, right):
                aux(left)
                aux(right)
            case Or(left, right):
                aux(left)
                aux(right)
            case Implies(left, right):
                aux(left)
                aux(right)
            case Eventually(g, _):
                aux(g)
            case Always(g, _):
                aux(g)
            case Until(left, right, _):
                aux(left)
                aux(right)
            case _:
                raise ValueError(f"Unsupported MITL construct: {f}")
        return label

    aux(f)
    return "\n".join(ltlspec_lines), subformulae
