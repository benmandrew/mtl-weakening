from dataclasses import dataclass

from src.logic import mtl


class Ctx:
    def __str__(self) -> str:
        return to_string(self)

    def __repr__(self) -> str:
        return to_string(self)


@dataclass(frozen=True, order=True, repr=False)
class Hole(Ctx):
    pass


@dataclass(frozen=True, order=True, repr=False)
class Not(Ctx):
    operand: Ctx


@dataclass(frozen=True, order=True, repr=False)
class AndLeft(Ctx):
    left: Ctx
    right: mtl.Mtl


@dataclass(frozen=True, order=True, repr=False)
class AndRight(Ctx):
    left: mtl.Mtl
    right: Ctx


@dataclass(frozen=True, order=True, repr=False)
class OrLeft(Ctx):
    left: Ctx
    right: mtl.Mtl


@dataclass(frozen=True, order=True, repr=False)
class OrRight(Ctx):
    left: mtl.Mtl
    right: Ctx


@dataclass(frozen=True, order=True, repr=False)
class ImpliesLeft(Ctx):
    left: Ctx
    right: mtl.Mtl


@dataclass(frozen=True, order=True, repr=False)
class ImpliesRight(Ctx):
    left: mtl.Mtl
    right: Ctx


@dataclass(frozen=True, order=True, repr=False)
class Next(Ctx):
    operand: Ctx


@dataclass(frozen=True, order=True, repr=False)
class Eventually(Ctx):
    operand: Ctx
    interval: mtl.Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class Always(Ctx):
    operand: Ctx
    interval: mtl.Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class UntilLeft(Ctx):
    left: Ctx
    right: mtl.Mtl
    interval: mtl.Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class UntilRight(Ctx):
    left: mtl.Mtl
    right: Ctx
    interval: mtl.Interval = (0, None)


def substitute(c: Ctx, f: mtl.Mtl) -> mtl.Mtl:
    if isinstance(c, Hole):
        return f
    if isinstance(c, Not):
        return mtl.Not(substitute(c.operand, f))
    if isinstance(c, AndLeft):
        return mtl.And(substitute(c.left, f), c.right)
    if isinstance(c, AndRight):
        return mtl.And(c.left, substitute(c.right, f))
    if isinstance(c, OrLeft):
        return mtl.Or(substitute(c.left, f), c.right)
    if isinstance(c, OrRight):
        return mtl.Or(c.left, substitute(c.right, f))
    if isinstance(c, ImpliesLeft):
        return mtl.Implies(substitute(c.left, f), c.right)
    if isinstance(c, ImpliesRight):
        return mtl.Implies(c.left, substitute(c.right, f))
    if isinstance(c, Next):
        return mtl.Next(substitute(c.operand, f))
    if isinstance(c, Eventually):
        return mtl.Eventually(substitute(c.operand, f), c.interval)
    if isinstance(c, Always):
        return mtl.Always(substitute(c.operand, f), c.interval)
    if isinstance(c, UntilLeft):
        return mtl.Until(substitute(c.left, f), c.right, c.interval)
    if isinstance(c, UntilRight):
        return mtl.Until(c.left, substitute(c.right, f), c.interval)
    raise ValueError(f"Unsupported MTL context construct: {c}")


def to_string(c: Ctx) -> str:
    if isinstance(c, Hole):
        return "[-]"
    if isinstance(c, Not):
        return f"!({to_string(c.operand)})"
    if isinstance(c, AndLeft):
        return f"({to_string(c.left)} & {mtl.to_string(c.right)})"
    if isinstance(c, AndRight):
        return f"({mtl.to_string(c.left)} & {to_string(c.right)})"
    if isinstance(c, OrLeft):
        return f"({to_string(c.left)} | {mtl.to_string(c.right)})"
    if isinstance(c, OrRight):
        return f"({mtl.to_string(c.left)} | {to_string(c.right)})"
    if isinstance(c, ImpliesLeft):
        return f"({to_string(c.left)} -> {mtl.to_string(c.right)})"
    if isinstance(c, ImpliesRight):
        return f"({mtl.to_string(c.left)} -> {to_string(c.right)})"
    if isinstance(c, Eventually):
        return f"F{mtl.fmt_interval(c.interval)} ({to_string(c.operand)})"
    if isinstance(c, Always):
        return f"G{mtl.fmt_interval(c.interval)} ({to_string(c.operand)})"
    if isinstance(c, UntilLeft):
        return (
            f"({to_string(c.left)} "
            f"U{mtl.fmt_interval(c.interval)} "
            f"{mtl.to_string(c.right)})"
        )
    if isinstance(c, UntilRight):
        return (
            f"({mtl.to_string(c.left)} "
            f"U{mtl.fmt_interval(c.interval)} "
            f"{to_string(c.right)})"
        )
    if isinstance(c, Next):
        return f"X ({to_string(c.operand)})"
    raise ValueError(f"Unsupported MTL context construct: {c}")


def _split_formula_aux(
    f: mtl.Mtl, indices: list[int], formula_idx: int
) -> tuple[Ctx, mtl.Mtl]:
    """
    Split the formula `f` at the given De Bruijn indices into a
    context and a formula. The context is the part of the formula
    that is not affected by the weakening.
    """
    if formula_idx == len(indices):
        return Hole(), f
    if isinstance(f, mtl.Prop):
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    if isinstance(f, mtl.Not):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.operand, indices, formula_idx + 1)
            return Not(ctx), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    if isinstance(f, mtl.And):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.left, indices, formula_idx + 1)
            return AndLeft(ctx, f.right), subf
        if indices[formula_idx] == 1:
            ctx, subf = _split_formula_aux(f.right, indices, formula_idx + 1)
            return AndRight(f.left, ctx), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    if isinstance(f, mtl.Or):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.left, indices, formula_idx + 1)
            return OrLeft(ctx, f.right), subf
        if indices[formula_idx] == 1:
            ctx, subf = _split_formula_aux(f.right, indices, formula_idx + 1)
            return OrRight(f.left, ctx), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    if isinstance(f, mtl.Implies):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.left, indices, formula_idx + 1)
            return ImpliesLeft(ctx, f.right), subf
        if indices[formula_idx] == 1:
            ctx, subf = _split_formula_aux(f.right, indices, formula_idx + 1)
            return ImpliesRight(f.left, ctx), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    if isinstance(f, mtl.Eventually):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.operand, indices, formula_idx + 1)
            return Eventually(ctx, f.interval), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    if isinstance(f, mtl.Always):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.operand, indices, formula_idx + 1)
            return Always(ctx, f.interval), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    if isinstance(f, mtl.Until):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.left, indices, formula_idx + 1)
            return UntilLeft(ctx, f.right, f.interval), subf
        if indices[formula_idx] == 1:
            ctx, subf = _split_formula_aux(f.right, indices, formula_idx + 1)
            return UntilRight(f.left, ctx, f.interval), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    raise ValueError(f"Unsupported MTL construct: {f}")


def split_formula(formula: mtl.Mtl, indices: list[int]) -> tuple[Ctx, mtl.Mtl]:
    return _split_formula_aux(formula, indices, 0)


def get_de_bruijn(c: Ctx) -> list[int]:
    """
    Get the De Bruijn indices of the context `c`.
    """
    if isinstance(c, Hole):
        return []
    if isinstance(c, (Not, Next, Eventually, Always)):
        return [0, *get_de_bruijn(c.operand)]
    if isinstance(c, (AndLeft, OrLeft, ImpliesLeft, UntilLeft)):
        return [0, *get_de_bruijn(c.left)]
    if isinstance(c, (AndRight, OrRight, ImpliesRight, UntilRight)):
        return [1, *get_de_bruijn(c.right)]
    raise ValueError(f"Unsupported MTL context construct: {c}")
