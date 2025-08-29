import unittest

import timeout_decorator

from src import marking, weaken
from src.logic import ctx, mtl, parser


class TestWeakenContext(unittest.TestCase):

    def test_weakening_fg(self) -> None:
        formula = parser.parse_mtl("F G[0,2] a")
        context, subformula = ctx.split_formula(formula, [0])
        trace = marking.Trace(
            [
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
                {"a": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_gf(self) -> None:
        formula = parser.parse_mtl("G F[0,4] a")
        context, subformula = ctx.split_formula(formula, [0])
        trace = marking.Trace(
            [
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            1,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 6))
        trace = marking.Trace(
            [
                {"a": True},
                {"a": False},
            ],
            1,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        self.assertIsNone(result)

    @timeout_decorator.timeout(1)  # type: ignore[misc]
    def test_weakening_gf_timeout(self) -> None:
        """
        Weakening should use the minimum of the interval and the trace length.
        If there is a timeout, it means we're probably
        trying to explore the entire interval here
        """
        formula = parser.parse_mtl("G[0,9999999999999999999] F[0,4] a")
        context, subformula = ctx.split_formula(formula, [0])
        trace = marking.Trace(
            [
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            1,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 6))

    def test_weakening_ff(self) -> None:
        formula = parser.parse_mtl("F (a & F[0,2] b)")
        context, subformula = ctx.split_formula(formula, [0, 1])
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 4))

    def test_weakening_gg(self) -> None:
        formula = parser.parse_mtl("G (a | G[0,2] b)")
        context, subformula = ctx.split_formula(formula, [0, 1])
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": True},
                {"a": True, "b": True},
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": True},
                {"a": False, "b": True},
                {"a": False, "b": True},
                {"a": True, "b": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_gfg(self) -> None:
        formula = parser.parse_mtl("G F G[2,5] a")
        context, subformula = ctx.split_formula(formula, [0, 0])
        trace = marking.Trace(
            [
                {"a": False},
                {"a": True},
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            2,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (2, 3))

    def test_weakening_gu(self) -> None:
        formula = parser.parse_mtl("G (a U[0,2] b)")
        context, subformula = ctx.split_formula(formula, [0])
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 5))

    def test_weakening_uf_right(self) -> None:
        formula = parser.parse_mtl("a U F[2,3] b")
        context, subformula = ctx.split_formula(formula, [1])
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (2, 7))

    def test_weakening_uf_left(self) -> None:
        formula = parser.parse_mtl("F[0,1] b U a")
        context, subformula = ctx.split_formula(formula, [0])
        trace = marking.Trace(
            [
                {"a": False, "b": True},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": True, "b": True},
            ],
            3,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))
        trace = marking.Trace(
            [
                {"a": False, "b": True},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": True, "b": False},
            ],
            3,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        self.assertIsNone(result)
        trace = marking.Trace(
            [
                {"a": True, "b": False},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_gug_right(self) -> None:
        formula = parser.parse_mtl("G (a U G[1,4] b)")
        context, subformula = ctx.split_formula(formula, [0, 1])
        trace = marking.Trace(
            [
                {"a": False, "b": False},
                {"a": True, "b": True},
                {"a": True, "b": True},
                {"a": True, "b": False},
                {"a": True, "b": False},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (1, 2))

    def test_weakening_gngf(self) -> None:
        formula = parser.parse_mtl("G ! G F[0,2] p")
        context, subformula = ctx.split_formula(formula, [0, 0, 0])
        assert isinstance(
            subformula,
            (mtl.Always, mtl.Eventually, mtl.Until, mtl.Release),
        )
        context, subformula = ctx.partial_nnf(context, subformula)
        trace = marking.Trace(
            [
                {"p": False},
                {"p": False},
                {"p": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_nfg(self) -> None:
        formula = parser.parse_mtl("! F G[0,1] p")
        context, subformula = ctx.split_formula(formula, [0, 0])
        assert isinstance(
            subformula,
            (mtl.Always, mtl.Eventually, mtl.Until, mtl.Release),
        )
        context, subformula = ctx.partial_nnf(context, subformula)
        trace = marking.Trace(
            [
                {"p": False},
                {"p": True},
                {"p": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))

    def test_weakening_ng(self) -> None:
        formula = parser.parse_mtl("! G[0,1] p")
        context, subformula = ctx.split_formula(formula, [0])
        assert isinstance(
            subformula,
            (mtl.Always, mtl.Eventually, mtl.Until, mtl.Release),
        )
        context, subformula = ctx.partial_nnf(context, subformula)
        trace = marking.Trace(
            [
                {"p": True},
                {"p": True},
                {"p": False},
            ],
            2,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))

    def test_weakening_rg_left(self) -> None:
        formula = parser.parse_mtl("G[0,2] a R b")
        context, subformula = ctx.split_formula(formula, [0])
        trace = marking.Trace(
            [
                {"a": True, "b": True},
                {"a": True, "b": False},
                {"a": False, "b": True},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_rf_right(self) -> None:
        formula = parser.parse_mtl("a R F[0,1] b")
        context, subformula = ctx.split_formula(formula, [1])
        trace = marking.Trace(
            [
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": True, "b": True},
                {"a": True, "b": False},
            ],
            4,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 3))
        trace = marking.Trace(
            [
                {"a": False, "b": True},
                {"a": False, "b": False},
            ],
            1,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        self.assertIsNone(result)
        trace = marking.Trace(
            [
                {"a": False, "b": False},
                {"a": False, "b": False},
                {"a": True, "b": True},
            ],
            1,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))


class TestWeakenDirect(unittest.TestCase):

    def test_weaken_direct_release_1(self) -> None:
        formula = parser.parse_mtl("b R[0,2] a")
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": False},
            ],
            0,
        )
        result = weaken.Weaken(
            ctx.Hole(),
            formula,
            trace,
        ).weaken()
        self.assertEqual(result, (0, 1))
        formula = parser.parse_mtl("a R[0,2] b")
        result = weaken.Weaken(
            ctx.Hole(),
            formula,
            trace,
        ).weaken()
        self.assertIsNone(result)

    def test_weaken_direct_release_2(self) -> None:
        formula = parser.parse_mtl("b R[0,2] a")
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": True},
                {"a": False, "b": False},
            ],
            0,
        )
        result = weaken.Weaken(
            ctx.Hole(),
            formula,
            trace,
        ).weaken()
        self.assertEqual(result, (0, 2))


if __name__ == "__main__":
    unittest.main()
