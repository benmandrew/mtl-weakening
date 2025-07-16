from dataclasses import dataclass


class Ltl:
    pass


@dataclass(frozen=True)
class Prop(Ltl):
    name: str


@dataclass(frozen=True)
class Not(Ltl):
    operand: Ltl


@dataclass(frozen=True)
class Next(Ltl):
    operand: Ltl


@dataclass(frozen=True)
class Eventually(Ltl):
    operand: Ltl


@dataclass(frozen=True)
class Always(Ltl):
    operand: Ltl


@dataclass(frozen=True)
class And(Ltl):
    left: Ltl
    right: Ltl


@dataclass(frozen=True)
class Or(Ltl):
    left: Ltl
    right: Ltl


@dataclass(frozen=True)
class Implies(Ltl):
    left: Ltl
    right: Ltl


@dataclass(frozen=True)
class Until(Ltl):
    left: Ltl
    right: Ltl


def to_nuxmv(formula: Ltl) -> str:
    match formula:
        case Prop(name):
            return name
        case Not(f):
            return f"!({to_nuxmv(f)})"
        case Next(f):
            return f"X ({to_nuxmv(f)})"
        case Eventually(f):
            return f"F ({to_nuxmv(f)})"
        case Always(f):
            return f"G ({to_nuxmv(f)})"
        case And(l, r):
            return f"({to_nuxmv(l)} & {to_nuxmv(r)})"
        case Or(l, r):
            return f"({to_nuxmv(l)} | {to_nuxmv(r)})"
        case Implies(l, r):
            return f"({to_nuxmv(l)} -> {to_nuxmv(r)})"
        case Until(l, r):
            return f"({to_nuxmv(l)} U {to_nuxmv(r)})"
        case _:
            raise ValueError(f"Unsupported LTL construct: {formula}")
