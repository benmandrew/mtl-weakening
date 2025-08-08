from __future__ import annotations

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


@dataclass(frozen=True, order=True, repr=False)
class ReleaseLeft(Ctx):
    left: Ctx
    right: mtl.Mtl
    interval: mtl.Interval = (0, None)


@dataclass(frozen=True, order=True, repr=False)
class ReleaseRight(Ctx):
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
    if isinstance(c, ReleaseLeft):
        return mtl.Release(substitute(c.left, f), c.right, c.interval)
    if isinstance(c, ReleaseRight):
        return mtl.Release(c.left, substitute(c.right, f), c.interval)
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
    if isinstance(c, ReleaseLeft):
        return (
            f"({to_string(c.left)} "
            f"R{mtl.fmt_interval(c.interval)} "
            f"{mtl.to_string(c.right)})"
        )
    if isinstance(c, ReleaseRight):
        return (
            f"({mtl.to_string(c.left)} "
            f"R{mtl.fmt_interval(c.interval)} "
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
    if isinstance(f, mtl.Release):
        if indices[formula_idx] == 0:
            ctx, subf = _split_formula_aux(f.left, indices, formula_idx + 1)
            return ReleaseLeft(ctx, f.right, f.interval), subf
        if indices[formula_idx] == 1:
            ctx, subf = _split_formula_aux(f.right, indices, formula_idx + 1)
            return ReleaseRight(f.left, ctx, f.interval), subf
        raise mtl.DeBruijnIndexError(indices, formula_idx, f)
    msg = f"Unsupported MTL construct: {f}"
    raise ValueError(msg)


def split_formula(formula: mtl.Mtl, indices: list[int]) -> tuple[Ctx, mtl.Mtl]:
    return _split_formula_aux(formula, indices, 0)


def _partial_nnf_ctx_neg(c: Ctx) -> tuple[Ctx, bool]:
    """Convert the negation of the context `c` to partial negation normal form (NNF)."""

    if isinstance(c, Hole):
        return c, False
    if isinstance(c, Not):
        operand, polarity = partial_nnf_ctx(c.operand)
        return operand, polarity
    if isinstance(c, AndLeft):
        left, polarity = _partial_nnf_ctx_neg(c.left)
        return OrLeft(left, mtl.Not(c.right)), polarity
    if isinstance(c, OrLeft):
        left, polarity = _partial_nnf_ctx_neg(c.left)
        return AndLeft(left, mtl.Not(c.right)), polarity
    if isinstance(c, ImpliesLeft):
        left, polarity = partial_nnf_ctx(c.left)
        return AndLeft(left, mtl.Not(c.right)), polarity
    if isinstance(c, UntilLeft):
        left, polarity = _partial_nnf_ctx_neg(c.left)
        return ReleaseLeft(left, mtl.Not(c.right), c.interval), polarity
    if isinstance(c, ReleaseLeft):
        left, polarity = _partial_nnf_ctx_neg(c.left)
        return UntilLeft(left, mtl.Not(c.right), c.interval), polarity
    if isinstance(c, AndRight):
        right, polarity = _partial_nnf_ctx_neg(c.right)
        return OrRight(mtl.Not(c.left), right), polarity
    if isinstance(c, OrRight):
        right, polarity = _partial_nnf_ctx_neg(c.right)
        return AndRight(mtl.Not(c.left), right), polarity
    if isinstance(c, ImpliesRight):
        right, polarity = _partial_nnf_ctx_neg(c.right)
        return AndRight(c.left, right), polarity
    if isinstance(c, UntilRight):
        right, polarity = _partial_nnf_ctx_neg(c.right)
        return ReleaseRight(mtl.Not(c.left), right, c.interval), polarity
    if isinstance(c, ReleaseRight):
        right, polarity = _partial_nnf_ctx_neg(c.right)
        return UntilRight(mtl.Not(c.left), right, c.interval), polarity
    if isinstance(c, Next):
        operand, polarity = _partial_nnf_ctx_neg(c.operand)
        return Next(operand), polarity
    if isinstance(c, Eventually):
        operand, polarity = _partial_nnf_ctx_neg(c.operand)
        return Always(operand, c.interval), polarity
    if isinstance(c, Always):
        operand, polarity = _partial_nnf_ctx_neg(c.operand)
        return Eventually(operand, c.interval), polarity
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)


def partial_nnf_ctx(c: Ctx) -> tuple[Ctx, bool]:
    """Convert the context `c` to partial negation normal form (NNF)."""

    if isinstance(c, Hole):
        return c, True
    if isinstance(c, Not):
        operand, polarity = _partial_nnf_ctx_neg(c.operand)
        return operand, polarity
    if isinstance(c, AndLeft):
        left, polarity = partial_nnf_ctx(c.left)
        return AndLeft(left, c.right), polarity
    if isinstance(c, OrLeft):
        left, polarity = partial_nnf_ctx(c.left)
        return OrLeft(left, c.right), polarity
    if isinstance(c, ImpliesLeft):
        left, polarity = _partial_nnf_ctx_neg(c.left)
        return OrLeft(left, c.right), polarity
    if isinstance(c, UntilLeft):
        left, polarity = partial_nnf_ctx(c.left)
        return UntilLeft(left, c.right, c.interval), polarity
    if isinstance(c, ReleaseLeft):
        left, polarity = partial_nnf_ctx(c.left)
        return ReleaseLeft(left, c.right, c.interval), polarity
    if isinstance(c, AndRight):
        right, polarity = partial_nnf_ctx(c.right)
        return AndRight(c.left, right), polarity
    if isinstance(c, OrRight):
        right, polarity = partial_nnf_ctx(c.right)
        return OrRight(c.left, right), polarity
    if isinstance(c, ImpliesRight):
        right, polarity = partial_nnf_ctx(c.right)
        return OrRight(mtl.Not(c.left), right), polarity
    if isinstance(c, UntilRight):
        right, polarity = partial_nnf_ctx(c.right)
        return UntilRight(c.left, right, c.interval), polarity
    if isinstance(c, ReleaseRight):
        right, polarity = partial_nnf_ctx(c.right)
        return ReleaseRight(c.left, right, c.interval), polarity
    if isinstance(c, Next):
        operand, polarity = partial_nnf_ctx(c.operand)
        return Next(operand), polarity
    if isinstance(c, Eventually):
        operand, polarity = partial_nnf_ctx(c.operand)
        return Eventually(operand, c.interval), polarity
    if isinstance(c, Always):
        operand, polarity = partial_nnf_ctx(c.operand)
        return Always(operand, c.interval), polarity
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)


def partial_nnf(
    c: Ctx,
    subf: mtl.Always | mtl.Eventually | mtl.Until | mtl.Release,
) -> tuple[Ctx, mtl.Mtl]:
    """Convert the context `c` and the subformula `subf` to partial negation
    normal form (PNNF). The returned context and subformula are logically
    equivalent to the original ones.
    """

    ctx, polarity = partial_nnf_ctx(c)
    if polarity:
        return ctx, subf
    if isinstance(subf, mtl.Always):
        return ctx, mtl.Eventually(mtl.Not(subf.operand), subf.interval)
    if isinstance(subf, mtl.Eventually):
        return ctx, mtl.Always(mtl.Not(subf.operand), subf.interval)
    if isinstance(subf, mtl.Until):
        return ctx, mtl.Release(
            mtl.Not(subf.left),
            mtl.Not(subf.right),
            subf.interval,
        )
    return ctx, mtl.Until(
        mtl.Not(subf.left),
        mtl.Not(subf.right),
        subf.interval,
    )


def get_de_bruijn(c: Ctx) -> list[int]:
    """Get the De Bruijn indices of the context `c`."""
    if isinstance(c, Hole):
        return []
    if isinstance(c, (Not, Next, Eventually, Always)):
        return [0, *get_de_bruijn(c.operand)]
    if isinstance(c, (AndLeft, OrLeft, ImpliesLeft, UntilLeft, ReleaseLeft)):
        return [0, *get_de_bruijn(c.left)]
    if isinstance(
        c,
        (AndRight, OrRight, ImpliesRight, UntilRight, ReleaseRight),
    ):
        return [1, *get_de_bruijn(c.right)]
    msg = f"Unsupported MTL context construct: {c}"
    raise ValueError(msg)
