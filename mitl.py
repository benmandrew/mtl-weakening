from dataclasses import dataclass
from typing import Optional, Tuple
import ltl


class Mitl:
    pass


@dataclass(frozen=True)
class Prop(Mitl):
    name: str


@dataclass(frozen=True)
class Not(Mitl):
    operand: Mitl


@dataclass(frozen=True)
class And(Mitl):
    left: Mitl
    right: Mitl


@dataclass(frozen=True)
class Or(Mitl):
    left: Mitl
    right: Mitl


@dataclass(frozen=True)
class Implies(Mitl):
    left: Mitl
    right: Mitl


@dataclass(frozen=True)
class Next(Mitl):
    operand: Mitl


@dataclass(frozen=True)
class Eventually(Mitl):
    operand: Mitl
    interval: Tuple[int, Optional[int]]


@dataclass(frozen=True)
class Always(Mitl):
    operand: Mitl
    interval: Tuple[int, Optional[int]]


@dataclass(frozen=True)
class Until(Mitl):
    left: Mitl
    right: Mitl
    interval: Tuple[int, Optional[int]]


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
            out = None
            if b is None:
                out = ltl.Eventually(subf)
            else:
                for _ in range(b - a + 1):
                    if out is None:
                        out = subf
                    else:
                        out = ltl.Or(subf, ltl.Next(out))
            for _ in range(a):
                out = ltl.Next(out)
            return out

        case Always(f, (a, b)):
            subf = mitl_to_ltl(f)
            out = None
            if b is None:
                out = ltl.Always(subf)
            else:
                for _ in range(b - a + 1):
                    if out is None:
                        out = subf
                    else:
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
                    out = None
                    for _ in range(i + 1):
                        if out is None:
                            out = right
                        else:
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
