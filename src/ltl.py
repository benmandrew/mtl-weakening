from dataclasses import dataclass
from src.util import matchable


@matchable
@dataclass(frozen=True, order=True)
class Ltl:
    pass


@matchable
@dataclass(frozen=True)
class Prop(Ltl):
    name: str


@matchable
@dataclass(frozen=True)
class Not(Ltl):
    operand: Ltl


@matchable
@dataclass(frozen=True)
class Next(Ltl):
    operand: Ltl


@matchable
@dataclass(frozen=True)
class Eventually(Ltl):
    operand: Ltl


@matchable
@dataclass(frozen=True)
class Always(Ltl):
    operand: Ltl


@matchable
@dataclass(frozen=True)
class And(Ltl):
    left: Ltl
    right: Ltl


@matchable
@dataclass(frozen=True)
class Or(Ltl):
    left: Ltl
    right: Ltl


@matchable
@dataclass(frozen=True)
class Implies(Ltl):
    left: Ltl
    right: Ltl


@matchable
@dataclass(frozen=True)
class Until(Ltl):
    left: Ltl
    right: Ltl


def to_nuxmv(formula: Ltl) -> str:
    if isinstance(formula, Prop):
        return formula.name
    elif isinstance(formula, Not):
        return f"!({to_nuxmv(formula.operand)})"
    elif isinstance(formula, Next):
        return f"X ({to_nuxmv(formula.operand)})"
    elif isinstance(formula, Eventually):
        return f"F ({to_nuxmv(formula.operand)})"
    elif isinstance(formula, Always):
        return f"G ({to_nuxmv(formula.operand)})"
    elif isinstance(formula, And):
        return f"({to_nuxmv(formula.left)} & {to_nuxmv(formula.right)})"
    elif isinstance(formula, Or):
        return f"({to_nuxmv(formula.left)} | {to_nuxmv(formula.right)})"
    elif isinstance(formula, Implies):
        return f"({to_nuxmv(formula.left)} -> {to_nuxmv(formula.right)})"
    elif isinstance(formula, Until):
        return f"({to_nuxmv(formula.left)} U {to_nuxmv(formula.right)})"
    else:
        raise ValueError(f"Unsupported LTL construct: {formula}")


def to_string(formula: Ltl) -> str:
    return to_nuxmv(formula)
