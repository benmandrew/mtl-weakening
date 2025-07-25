from dataclasses import dataclass

from src.logic import mtl


class Ctx:
    def __str__(self) -> str:
        return to_string(self)

    def __repr__(self) -> str:
        return to_string(self)


@dataclass(frozen=True, order=True, repr=False)
class CtxHole(Ctx):
    name: str


@dataclass(frozen=True, order=True, repr=False)
class CtxNot(Ctx):
    operand: Ctx


@dataclass(frozen=True, order=True, repr=False)
class CtxAndLeft(Ctx):
    left: Ctx
    right: mtl.Mtl


@dataclass(frozen=True, order=True, repr=False)
class CtxAndRight(Ctx):
    left: mtl.Mtl
    right: Ctx


@dataclass(frozen=True, order=True, repr=False)
class CtxOrLeft(Ctx):
    left: Ctx
    right: mtl.Mtl


@dataclass(frozen=True, order=True, repr=False)
class CtxOrRight(Ctx):
    left: mtl.Mtl
    right: Ctx


@dataclass(frozen=True, order=True, repr=False)
class CtxImpliesLeft(Ctx):
    left: Ctx
    right: mtl.Mtl


@dataclass(frozen=True, order=True, repr=False)
class CtxImpliesRight(Ctx):
    left: mtl.Mtl
    right: Ctx


@dataclass(frozen=True, order=True, repr=False)
class CtxNext(Ctx):
    operand: Ctx


@dataclass(frozen=True, order=True, repr=False)
class CtxEventually(Ctx):
    operand: Ctx
    interval: mtl.Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class CtxAlways(Ctx):
    operand: Ctx
    interval: mtl.Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class CtxUntilLeft(Ctx):
    left: Ctx
    right: mtl.Mtl
    interval: mtl.Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class CtxUntilRight(Ctx):
    left: mtl.Mtl
    right: Ctx
    interval: mtl.Interval = (0, None)


def substitute(c: Ctx, f: mtl.Mtl) -> mtl.Mtl:
    if isinstance(c, CtxHole):
        return f
    if isinstance(c, CtxNot):
        return mtl.Not(substitute(c.operand, f))
    if isinstance(c, CtxAndLeft):
        return mtl.And(substitute(c.left, f), c.right)
    if isinstance(c, CtxAndRight):
        return mtl.And(c.left, substitute(c.right, f))
    if isinstance(c, CtxOrLeft):
        return mtl.Or(substitute(c.left, f), c.right)
    if isinstance(c, CtxOrRight):
        return mtl.Or(c.left, substitute(c.right, f))
    if isinstance(c, CtxImpliesLeft):
        return mtl.Implies(substitute(c.left, f), c.right)
    if isinstance(c, CtxImpliesRight):
        return mtl.Implies(c.left, substitute(c.right, f))
    if isinstance(c, CtxNext):
        return mtl.Next(substitute(c.operand, f))
    if isinstance(c, CtxEventually):
        return mtl.Eventually(substitute(c.operand, f), c.interval)
    if isinstance(c, CtxAlways):
        return mtl.Always(substitute(c.operand, f), c.interval)
    if isinstance(c, CtxUntilLeft):
        return mtl.Until(substitute(c.left, f), c.right, c.interval)
    if isinstance(c, CtxUntilRight):
        return mtl.Until(c.left, substitute(c.right, f), c.interval)
    raise ValueError(f"Unsupported MTL context construct: {c}")


def to_string(c: Ctx) -> str:
    if isinstance(c, CtxHole):
        return "[-]"
    if isinstance(c, CtxNot):
        return f"!({to_string(c.operand)})"
    if isinstance(c, CtxAndLeft):
        return f"({to_string(c.left)} & {mtl.to_string(c.right)})"
    if isinstance(c, CtxAndRight):
        return f"({mtl.to_string(c.left)} & {to_string(c.right)})"
    if isinstance(c, CtxOrLeft):
        return f"({to_string(c.left)} | {mtl.to_string(c.right)})"
    if isinstance(c, CtxOrRight):
        return f"({mtl.to_string(c.left)} | {to_string(c.right)})"
    if isinstance(c, CtxImpliesLeft):
        return f"({to_string(c.left)} -> {mtl.to_string(c.right)})"
    if isinstance(c, CtxImpliesRight):
        return f"({mtl.to_string(c.left)} -> {to_string(c.right)})"
    if isinstance(c, CtxEventually):
        return f"F{mtl.fmt_interval(c.interval)} ({to_string(c.operand)})"
    if isinstance(c, CtxAlways):
        return f"G{mtl.fmt_interval(c.interval)} ({to_string(c.operand)})"
    if isinstance(c, CtxUntilLeft):
        return (
            f"({to_string(c.left)} "
            f"U{mtl.fmt_interval(c.interval)} "
            f"{mtl.to_string(c.right)})"
        )
    if isinstance(c, CtxUntilRight):
        return (
            f"({mtl.to_string(c.left)} "
            f"U{mtl.fmt_interval(c.interval)} "
            f"{to_string(c.right)})"
        )
    if isinstance(c, CtxNext):
        return f"X ({to_string(c.operand)})"
    raise ValueError(f"Unsupported MTL context construct: {c}")
