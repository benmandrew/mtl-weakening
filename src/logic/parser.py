from __future__ import annotations

import pathlib

import lark

from src.logic import mtl


@lark.v_args(inline=True)
class MTLTransformer(lark.Transformer):
    def start(self, *args: mtl.Mtl) -> mtl.Mtl:
        return args[0]

    def INT(self, value: lark.Token) -> int:  # noqa: N802
        return int(str(value))

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

    def until(self, left: mtl.Mtl, *rest: mtl.Interval | mtl.Mtl) -> mtl.Until:
        """
        Handles left-associative chaining of Until operators:
        - until φ U ψ
        - until φ U[0,4] ψ
        - until φ U ψ U[1,3] χ
        etc.
        """
        node = left
        it = iter(rest)
        while True:
            try:
                first = next(it)
            except StopIteration:
                break
            try:
                second = next(it)
            except StopIteration:
                assert isinstance(first, mtl.Mtl), "Expected an MTL node"
                rhs = first
                interval: mtl.Interval = (0, None)
            else:
                if isinstance(first, tuple):
                    assert isinstance(second, mtl.Mtl), "Expected an MTL node"
                    interval = first
                    rhs = second
                else:
                    interval = (0, None)
                    rhs = first
                    # put `second` back into iterator
                    it = (x for x in (second, *it))
            node = mtl.Until(node, rhs, interval)
        assert isinstance(node, mtl.Until), "Expected an MTL Until node"
        return node

    def _split_interval_args(
        self,
        args: tuple,
    ) -> tuple[mtl.Interval, mtl.Mtl]:
        if len(args) == 1:
            return (0, None), args[0]
        if len(args) == 2:  # noqa: PLR2004
            interval, phi = args
            if not isinstance(interval, tuple):
                return (0, None), interval
            return interval, phi
        msg = "Unexpected arity for temporal operator."
        raise ValueError(msg)


PARSER_PATH = pathlib.Path("src/logic/mtl.lark")
with PARSER_PATH.open(encoding="utf-8") as f:
    grammar = f.read()
MTL_PARSER = lark.Lark(grammar, start="start", parser="lalr")


def parse_mtl(text: str) -> mtl.Mtl:
    """
    Parse an MTL formula string into a validated AST.
    Returns a Python dict tree; raises ValueError / UnexpectedInput on errors.
    """
    tree = MTL_PARSER.parse(text)
    return MTLTransformer().transform(tree)
