from __future__ import annotations

from pathlib import Path

import lark

from src.logic import ltl, mtl


@lark.v_args(inline=True)
class MTLTransformer(lark.Transformer[lark.Token, mtl.Mtl]):
    def start(self, *args: mtl.Mtl) -> mtl.Mtl:
        return args[0]

    def INT(  # noqa: N802 pylint: disable=invalid-name
        self,
        value: lark.Token,
    ) -> int:
        return int(str(value))

    def true(self) -> mtl.TrueBool:
        return mtl.TrueBool()

    def false(self) -> mtl.FalseBool:
        return mtl.FalseBool()

    def ap(self, name: lark.Token) -> mtl.Prop:
        return mtl.Prop(str(name))

    def neg(self, phi: mtl.Mtl) -> mtl.Not:
        return mtl.Not(phi)

    def conjunction(self, left: mtl.Mtl, right: mtl.Mtl) -> mtl.And:
        return mtl.And(left=left, right=right)

    def disjunction(self, left: mtl.Mtl, right: mtl.Mtl) -> mtl.Or:
        return mtl.Or(left=left, right=right)

    def implies(self, left: mtl.Mtl, right: mtl.Mtl) -> mtl.Implies:
        return mtl.Implies(left=left, right=right)

    def maybe_infinity(self, value: lark.Token | None = None) -> int | None:
        if value is None:
            return None
        return int(str(value))

    def interval(self, m: int, n: int | None) -> mtl.Interval:
        if m < 0 or (isinstance(n, int) and n < 0):
            msg = f"Interval bounds must be natural numbers: [{m},{n}]"
            raise ValueError(
                msg,
            )
        if isinstance(n, int) and m > n:
            msg = f"Interval lower bound must be ≤ upper bound: [{m},{n}]"
            raise ValueError(
                msg,
            )
        return (m, n)

    def always(
        self,
        *args: mtl.Mtl | tuple[mtl.Interval, mtl.Mtl],
    ) -> mtl.Always:
        interval, phi = self._split_interval_args(args)
        return mtl.Always(phi, interval)

    def eventually(
        self,
        *args: mtl.Mtl | tuple[mtl.Interval, mtl.Mtl],
    ) -> mtl.Eventually:
        interval, phi = self._split_interval_args(args)
        return mtl.Eventually(phi, interval)

    def next(self, phi: mtl.Mtl) -> mtl.Next:
        return mtl.Next(phi)

    def until(
        self,
        left: mtl.Mtl,
        *args: mtl.Mtl | tuple[mtl.Interval, mtl.Mtl],
    ) -> mtl.Until:
        interval, right = self._split_interval_args(args)
        return mtl.Until(left, right, interval)

    def release(
        self,
        left: mtl.Mtl,
        *args: mtl.Mtl | tuple[mtl.Interval, mtl.Mtl],
    ) -> mtl.Release:
        interval, right = self._split_interval_args(args)
        return mtl.Release(left, right, interval)

    def _split_interval_args(
        self,
        args: tuple[mtl.Mtl | tuple[mtl.Interval, mtl.Mtl], ...],
    ) -> tuple[mtl.Interval, mtl.Mtl]:
        # Craziness to get the mypy type checker happy
        if len(args) == 1:
            assert isinstance(args[0], mtl.Mtl)
            return (0, None), args[0]
        if len(args) == 2:  # noqa: PLR2004
            interval, phi = args
            if not isinstance(interval, tuple):
                return (0, None), interval
            assert (
                isinstance(interval, tuple)
                and isinstance(interval[0], int)
                and isinstance(interval[1], int | None)
            )
            assert isinstance(phi, mtl.Mtl)
            return interval, phi
        msg = "Unexpected arity for temporal operator."
        raise ValueError(msg)


with (Path(__file__).parent / "mtl.lark").open(encoding="utf-8") as f:
    grammar = f.read()
MTL_PARSER = lark.Lark(grammar, start="start", parser="lalr")


def parse_mtl(text: str) -> mtl.Mtl:
    """
    Parse an MTL formula string into a validated AST.
    """
    tree = MTL_PARSER.parse(text)
    return MTLTransformer().transform(tree)


@lark.v_args(inline=True)
class LTLTransformer(lark.Transformer[lark.Token, ltl.Ltl]):
    def start(self, *args: ltl.Ltl) -> ltl.Ltl:
        return args[0]

    def INT(  # noqa: N802 pylint: disable=invalid-name
        self,
        value: lark.Token,
    ) -> int:
        return int(str(value))

    def true(self) -> ltl.TrueBool:
        return ltl.TrueBool()

    def false(self) -> ltl.FalseBool:
        return ltl.FalseBool()

    def ap(self, name: lark.Token) -> ltl.Prop:
        return ltl.Prop(str(name))

    def neg(self, phi: ltl.Ltl) -> ltl.Not:
        return ltl.Not(phi)

    def conjunction(self, left: ltl.Ltl, right: ltl.Ltl) -> ltl.And:
        return ltl.And(left=left, right=right)

    def disjunction(self, left: ltl.Ltl, right: ltl.Ltl) -> ltl.Or:
        return ltl.Or(left=left, right=right)

    def implies(self, left: ltl.Ltl, right: ltl.Ltl) -> ltl.Implies:
        return ltl.Implies(left=left, right=right)

    def always(
        self,
        phi: ltl.Ltl,
    ) -> ltl.Always:
        return ltl.Always(phi)

    def eventually(
        self,
        phi: ltl.Ltl,
    ) -> ltl.Eventually:
        return ltl.Eventually(phi)

    def next(self, phi: ltl.Ltl) -> ltl.Next:
        return ltl.Next(phi)

    def until(
        self,
        left: ltl.Ltl,
        right: ltl.Ltl,
    ) -> ltl.Until:
        return ltl.Until(left, right)

    def release(
        self,
        left: ltl.Ltl,
        right: ltl.Ltl,
    ) -> ltl.Release:
        return ltl.Release(left, right)


with (Path(__file__).parent / "ltl_nuxmv.lark").open(encoding="utf-8") as f:
    grammar = f.read()
NUXMV_LTL_PARSER = lark.Lark(grammar, start="start", parser="lalr")


def parse_nuxmv_ltl(text: str) -> ltl.Ltl:
    """
    Parse an LTL formula string in NuXmv format into a validated AST.
    """
    tree = NUXMV_LTL_PARSER.parse(text)
    return LTLTransformer().transform(tree)


with (Path(__file__).parent / "ltl_spin.lark").open(encoding="utf-8") as f:
    grammar = f.read()
SPIN_LTL_PARSER = lark.Lark(grammar, start="start", parser="lalr")


def parse_spin_ltl(text: str) -> ltl.Ltl:
    """
    Parse an LTL formula string in Promela format into a validated AST.
    """
    tree = SPIN_LTL_PARSER.parse(text)
    return LTLTransformer().transform(tree)
