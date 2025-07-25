import unittest

from src.logic import ctx, mtl


class TestSplitFormula(unittest.TestCase):
    def test_deeply_nested_and_or(self):
        expected_context = ctx.AndLeft(
            ctx.OrRight(mtl.Prop("a"), ctx.Not(ctx.Hole())),
            mtl.Eventually(mtl.Prop("c")),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 1, 0])
        expected_subf = mtl.Always(mtl.Prop("b"))
        expected_f = mtl.And(
            mtl.Or(mtl.Prop("a"), mtl.Not(mtl.Always(mtl.Prop("b")))),
            mtl.Eventually(mtl.Prop("c")),
        )
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        result_context, result_subf = ctx.split_formula(expected_f, [0, 1, 0])
        self.assertEqual(expected_context, result_context)
        self.assertEqual(expected_subf, result_subf)

    def test_deeply_nested_until_and(self):
        expected_context = ctx.UntilLeft(
            ctx.AndRight(mtl.Prop("a"), ctx.Hole()),
            mtl.Or(mtl.Prop("c"), mtl.Prop("d")),
            (0, 5),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 1])
        expected_subf = mtl.Until(
            mtl.Eventually(mtl.Prop("b")), mtl.Prop("e"), (0, 3)
        )
        expected_f = mtl.Until(
            mtl.And(
                mtl.Prop("a"),
                mtl.Until(mtl.Eventually(mtl.Prop("b")), mtl.Prop("e"), (0, 3)),
            ),
            mtl.Or(mtl.Prop("c"), mtl.Prop("d")),
            (0, 5),
        )
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        context, subf = ctx.split_formula(result_f, indices)
        self.assertEqual(expected_context, context)
        self.assertEqual(expected_subf, subf)

    def test_deeply_nested_temporal_and_complex_subformula(self):
        expected_context = ctx.Eventually(
            ctx.AndLeft(
                ctx.UntilRight(mtl.Prop("a"), ctx.Hole(), (1, 3)),
                mtl.Or(mtl.Prop("b"), mtl.Prop("c")),
            ),
            (0, 5),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 0, 1])
        expected_subf = mtl.Always(
            mtl.And(
                mtl.Until(mtl.Prop("c"), mtl.Eventually(mtl.Prop("d")), (2, 4)),
                mtl.Or(mtl.Prop("e"), mtl.Prop("f")),
            )
        )
        expected_f = mtl.Eventually(
            mtl.And(
                mtl.Until(
                    mtl.Prop("a"),
                    mtl.Always(
                        mtl.And(
                            mtl.Until(
                                mtl.Prop("c"),
                                mtl.Eventually(mtl.Prop("d")),
                                (2, 4),
                            ),
                            mtl.Or(mtl.Prop("e"), mtl.Prop("f")),
                        )
                    ),
                    (1, 3),
                ),
                mtl.Or(mtl.Prop("b"), mtl.Prop("c")),
            ),
            (0, 5),
        )
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        context, subf = ctx.split_formula(expected_f, indices)
        self.assertEqual(expected_context, context)
        self.assertEqual(expected_subf, subf)


if __name__ == "__main__":
    unittest.main()
