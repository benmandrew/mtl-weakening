import unittest

from src import marking, mtl, weaken


class TestWeaken(unittest.TestCase):

    def test_weakening_fg(self):
        formula = mtl.Eventually(mtl.Always(mtl.Prop("a"), (0, 2)))
        indices = [0]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_gf(self):
        formula = mtl.Always(mtl.Eventually(mtl.Prop("a"), (0, 4)))
        indices = [0]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 6))
        trace = marking.Trace(
            [
                {"a": True},
                {"a": False},
            ],
            1,
        )
        result = weaken.Weaken(formula, indices, trace).weaken()
        self.assertIsNone(result)

    def test_weakening_ff(self):
        formula = mtl.Eventually(
            mtl.And(mtl.Prop("a"), mtl.Eventually(mtl.Prop("b"), (0, 2)))
        )
        indices = [0, 1]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 4))

    def test_weakening_gg(self):
        formula = mtl.Always(
            mtl.Or(mtl.Prop("a"), mtl.Always(mtl.Prop("b"), (0, 2)))
        )
        indices = [0, 1]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_gfg(self):
        formula = mtl.Always(mtl.Eventually(mtl.Always(mtl.Prop("a"), (2, 5))))
        indices = [0, 0]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (2, 3))

    def test_weakening_gu(self):
        formula = mtl.Always(mtl.Until(mtl.Prop("a"), mtl.Prop("b"), (0, 2)))
        indices = [0]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 5))

    def test_weakening_uf_right(self):
        formula = mtl.Until(
            mtl.Prop("a"), mtl.Eventually(mtl.Prop("b"), (2, 3))
        )
        indices = [1]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (2, 7))

    def test_weakening_ug_left(self):
        formula = mtl.Until(mtl.Always(mtl.Prop("a"), (0, 4)), mtl.Prop("b"))
        indices = [0]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))

    def test_weakening_gug_right(self):
        formula = mtl.Always(
            mtl.Until(mtl.Prop("a"), mtl.Always(mtl.Prop("b"), (1, 4)))
        )
        indices = [0, 1]
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
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (1, 2))

    def test_weakening_gngf(self):
        formula = mtl.Always(
            mtl.Not(mtl.Always(mtl.Eventually(mtl.Prop("p"), (0, 2))))
        )
        indices = [0, 0, 0]
        trace = marking.Trace(
            [
                {"p": False},
                {"p": False},
                {"p": True},
            ],
            0,
        )
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 1))

    def test_weakening_nfg(self):
        formula = mtl.Not(mtl.Eventually(mtl.Always(mtl.Prop("p"), (0, 1))))
        indices = [0, 0]
        trace = marking.Trace(
            [
                {"p": False},
                {"p": True},
                {"p": True},
            ],
            0,
        )
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))

    def test_weakening_ng(self):
        formula = mtl.Not(mtl.Always(mtl.Prop("p"), (0, 1)))
        indices = [0]
        trace = marking.Trace(
            [
                {"p": True},
                {"p": True},
                {"p": False},
            ],
            2,
        )
        result = weaken.Weaken(formula, indices, trace).weaken()
        assert result is not None
        self.assertTupleEqual(result, (0, 2))


if __name__ == "__main__":
    unittest.main()
