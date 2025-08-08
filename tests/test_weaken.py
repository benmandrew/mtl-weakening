import unittest

from src import marking, weaken
from src.logic import ctx, mtl


class TestWeakenContext(unittest.TestCase):

    def test_weakening_fg(self) -> None:
        formula = mtl.Eventually(mtl.Always(mtl.Prop("a"), (0, 2)))
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
        formula = mtl.Always(mtl.Eventually(mtl.Prop("a"), (0, 4)))
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

    def test_weakening_ff(self) -> None:
        formula = mtl.Eventually(
            mtl.And(mtl.Prop("a"), mtl.Eventually(mtl.Prop("b"), (0, 2))),
        )
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
        formula = mtl.Always(
            mtl.Or(mtl.Prop("a"), mtl.Always(mtl.Prop("b"), (0, 2))),
        )
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
        formula = mtl.Always(mtl.Eventually(mtl.Always(mtl.Prop("a"), (2, 5))))
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
        formula = mtl.Always(mtl.Until(mtl.Prop("a"), mtl.Prop("b"), (0, 2)))
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
        formula = mtl.Until(
            mtl.Prop("a"),
            mtl.Eventually(mtl.Prop("b"), (2, 3)),
        )
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

    def test_weakening_ug_left(self) -> None:
        formula = mtl.Until(mtl.Always(mtl.Prop("a"), (0, 4)), mtl.Prop("b"))
        context, subformula = ctx.split_formula(formula, [0])
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": True, "b": True},
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": False},
            ],
            0,
        )
        result = weaken.Weaken(context, subformula, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))

    def test_weakening_gug_right(self) -> None:
        formula = mtl.Always(
            mtl.Until(mtl.Prop("a"), mtl.Always(mtl.Prop("b"), (1, 4))),
        )
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
        formula = mtl.Always(
            mtl.Not(mtl.Always(mtl.Eventually(mtl.Prop("p"), (0, 2)))),
        )
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
        formula = mtl.Not(mtl.Eventually(mtl.Always(mtl.Prop("p"), (0, 1))))
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
        formula = mtl.Not(mtl.Always(mtl.Prop("p"), (0, 1)))
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


class TestWeakenDirect(unittest.TestCase):

    def test_weaken_direct_release_1(self) -> None:
        formula = mtl.Release(mtl.Prop("b"), mtl.Prop("a"), (0, 2))
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
        formula = mtl.Release(mtl.Prop("a"), mtl.Prop("b"), (0, 2))
        result = weaken.Weaken(
            ctx.Hole(),
            formula,
            trace,
        ).weaken()
        self.assertIsNone(result)

    def test_weaken_direct_release_2(self) -> None:
        formula = mtl.Release(mtl.Prop("b"), mtl.Prop("a"), (0, 2))
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
