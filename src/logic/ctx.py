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
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)


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
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)


def _split_formula_aux(
    f: mtl.Mtl,
    indices: list[int],
    formula_idx: int,
) -> tuple[Ctx, mtl.Mtl]:
    """Split the formula `f` at the given De Bruijn indices into a
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
    msg = f"Unsupported MTL construct: {f}"
    raise ValueError(msg)


def split_formula(formula: mtl.Mtl, indices: list[int]) -> tuple[Ctx, mtl.Mtl]:
    return _split_formula_aux(formula, indices, 0)


def _partial_nnf_neg(c: Ctx) -> Ctx:
    """Convert the negation of the context `c` to partial negation normal form (NNF)."""

    if isinstance(c, Hole):
        return Not(c)
    if isinstance(c, Not):
        return partial_nnf(c.operand)
    if isinstance(c, AndLeft):
        return OrLeft(partial_nnf(Not(c.left)), mtl.Not(c.right))
    if isinstance(c, OrLeft):
        return AndLeft(partial_nnf(Not(c.left)), mtl.Not(c.right))
    if isinstance(c, ImpliesLeft):
        return AndLeft(partial_nnf(c.left), mtl.Not(c.right))
    if isinstance(c, UntilLeft):
        raise NotImplementedError
        # left, polarity = partial_nnf(Not(c.left))
        # return UntilLeft(left, Not(c.right), c.interval), polarity
    if isinstance(c, AndRight):
        return OrRight(mtl.Not(c.left), partial_nnf(Not(c.right)))
    if isinstance(c, OrRight):
        return AndRight(mtl.Not(c.left), partial_nnf(Not(c.right)))
    if isinstance(c, ImpliesRight):
        return AndRight(c.left, partial_nnf(Not(c.right)))
    if isinstance(c, UntilRight):
        raise NotImplementedError
        # right, polarity = partial_nnf(Not(c.right))
        # return UntilRight(c.left, right, c.interval), polarity
    if isinstance(c, Next):
        return Next(partial_nnf(Not(c.operand)))
    if isinstance(c, Eventually):
        return Always(partial_nnf(Not(c.operand)), c.interval)
    if isinstance(c, Always):
        return Eventually(partial_nnf(Not(c.operand)), c.interval)
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)


def partial_nnf(c: Ctx) -> Ctx:
    """Convert the context `c` to partial negation normal form (NNF)."""

    if isinstance(c, Hole):
        return c
    if isinstance(c, Not):
        return _partial_nnf_neg(c.operand)
    if isinstance(c, AndLeft):
        return AndLeft(partial_nnf(c.left), c.right)
    if isinstance(c, OrLeft):
        return OrLeft(partial_nnf(c.left), c.right)
    if isinstance(c, ImpliesLeft):
        return ImpliesLeft(partial_nnf(c.left), c.right)
    if isinstance(c, UntilLeft):
        return UntilLeft(partial_nnf(c.left), c.right, c.interval)
    if isinstance(c, AndRight):
        return AndRight(c.left, partial_nnf(c.right))
    if isinstance(c, OrRight):
        return OrRight(c.left, partial_nnf(c.right))
    if isinstance(c, ImpliesRight):
        return ImpliesRight(c.left, partial_nnf(c.right))
    if isinstance(c, UntilRight):
        return UntilRight(c.left, partial_nnf(c.right), c.interval)
    if isinstance(c, Next):
        return Next(partial_nnf(c.operand))
    if isinstance(c, Eventually):
        return Eventually(partial_nnf(c.operand), c.interval)
    if isinstance(c, Always):
        return Always(partial_nnf(c.operand), c.interval)
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)


def get_de_bruijn(c: Ctx) -> list[int]:
    """Get the De Bruijn indices of the context `c`."""
    if isinstance(c, Hole):
        return []
    if isinstance(c, (Not, Next, Eventually, Always)):
        return [0, *get_de_bruijn(c.operand)]
    if isinstance(c, (AndLeft, OrLeft, ImpliesLeft, UntilLeft)):
        return [0, *get_de_bruijn(c.left)]
    if isinstance(c, (AndRight, OrRight, ImpliesRight, UntilRight)):
        return [1, *get_de_bruijn(c.right)]
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)
