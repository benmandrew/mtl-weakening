from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Ltl:
    pass


@dataclass(frozen=True)
class TrueBool(Ltl):
    pass


@dataclass(frozen=True)
class FalseBool(Ltl):
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


@dataclass(frozen=True)
class Release(Ltl):
    left: Ltl
    right: Ltl


def to_nuxmv(formula: Ltl) -> str:
    if isinstance(formula, TrueBool):
        return "TRUE"
    if isinstance(formula, FalseBool):
        return "FALSE"
    if isinstance(formula, Prop):
        return formula.name
    if isinstance(formula, Not):
        return f"!({to_nuxmv(formula.operand)})"
    if isinstance(formula, Next):
        return f"X ({to_nuxmv(formula.operand)})"
    if isinstance(formula, Eventually):
        return f"F ({to_nuxmv(formula.operand)})"
    if isinstance(formula, Always):
        return f"G ({to_nuxmv(formula.operand)})"
    if isinstance(formula, And):
        return f"({to_nuxmv(formula.left)} & {to_nuxmv(formula.right)})"
    if isinstance(formula, Or):
        return f"({to_nuxmv(formula.left)} | {to_nuxmv(formula.right)})"
    if isinstance(formula, Implies):
        return f"({to_nuxmv(formula.left)} -> {to_nuxmv(formula.right)})"
    if isinstance(formula, Until):
        return f"({to_nuxmv(formula.left)} U {to_nuxmv(formula.right)})"
    if isinstance(formula, Release):
        return f"({to_nuxmv(formula.left)} R {to_nuxmv(formula.right)})"
    msg = f"Unsupported LTL construct: {formula}"
    raise ValueError(msg)


def to_spin(formula: Ltl) -> str:
    if isinstance(formula, TrueBool):
        return "true"
    if isinstance(formula, FalseBool):
        return "false"
    if isinstance(formula, Prop):
        return formula.name
    if isinstance(formula, Not):
        return f"!({to_spin(formula.operand)})"
    if isinstance(formula, Next):
        return f"X ({to_spin(formula.operand)})"
    if isinstance(formula, Eventually):
        return f"<> ({to_spin(formula.operand)})"
    if isinstance(formula, Always):
        return f"[] ({to_spin(formula.operand)})"
    if isinstance(formula, And):
        return f"({to_spin(formula.left)} && {to_spin(formula.right)})"
    if isinstance(formula, Or):
        return f"({to_spin(formula.left)} || {to_spin(formula.right)})"
    if isinstance(formula, Implies):
        return f"({to_spin(formula.left)} -> {to_spin(formula.right)})"
    if isinstance(formula, Until):
        return f"({to_spin(formula.left)} U {to_spin(formula.right)})"
    if isinstance(formula, Release):
        return f"({to_spin(formula.left)} V {to_spin(formula.right)})"
    msg = f"Unsupported LTL construct: {formula}"
    raise ValueError(msg)


def to_string(formula: Ltl) -> str:
    return to_nuxmv(formula)
