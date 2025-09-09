import unittest

from src.logic import ctx, mtl, parser


class TestSplitFormula(unittest.TestCase):
    def test_deeply_nested_and_or(self) -> None:
        expected_context = ctx.AndLeft(
            ctx.OrRight(mtl.Prop("a"), ctx.Not(ctx.Hole())),
            mtl.Eventually(mtl.Prop("c")),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 1, 0])
        expected_subf = parser.parse_mtl("G b")
        expected_f = parser.parse_mtl("(a | !G b) & F c")
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        result_context, result_subf = ctx.split_formula(expected_f, [0, 1, 0])
        self.assertEqual(expected_context, result_context)
        self.assertEqual(expected_subf, result_subf)

    def test_deeply_nested_until_and(self) -> None:
        expected_context = ctx.UntilLeft(
            ctx.AndRight(mtl.Prop("a"), ctx.Hole()),
            mtl.Or(mtl.Prop("c"), mtl.Prop("d")),
            (0, 5),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 1])
        expected_subf = parser.parse_mtl("(F b) U[0,3] e")
        expected_f = parser.parse_mtl("(a & ((F b) U[0,3] e)) U[0,5] (c | d)")
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        context, subf = ctx.split_formula(result_f, indices)
        self.assertEqual(expected_context, context)
        self.assertEqual(expected_subf, subf)

    def test_deeply_nested_temporal_and_complex_subformula(self) -> None:
        expected_context = ctx.Eventually(
            ctx.AndLeft(
                ctx.UntilRight(mtl.Prop("a"), ctx.Hole(), (1, 3)),
                mtl.Or(mtl.Prop("b"), mtl.Prop("c")),
            ),
            (0, 5),
        )
        indices = ctx.get_de_bruijn(expected_context)
        self.assertEqual(indices, [0, 0, 1])
        expected_subf = parser.parse_mtl("G ((c U[2,4] F d) & (e | f))")
        expected_f = parser.parse_mtl(
            "F[0,5] ((a U[1,3] G ((c U[2,4] F d) & (e | f))) & (b | c))",
        )
        result_f = ctx.substitute(expected_context, expected_subf)
        self.assertEqual(expected_f, result_f)
        context, subf = ctx.split_formula(expected_f, indices)
        self.assertEqual(expected_context, context)
        self.assertEqual(expected_subf, subf)


class TestPartialNNFContext(unittest.TestCase):
    def test_complex_boolean_operators_nnf(self) -> None:
        """Test NNF conversion for complex nested boolean operators."""
        context = ctx.Not(
            ctx.OrRight(
                mtl.Prop("p"),
                ctx.AndLeft(ctx.Not(ctx.Hole()), mtl.Prop("q")),
            ),
        )
        expected_context = ctx.AndRight(
            mtl.Not(mtl.Prop("p")),
            ctx.OrLeft(ctx.Hole(), mtl.Not(mtl.Prop("q"))),
        )
        result_context, polarity = ctx.partial_nnf_ctx(context)
        self.assertEqual(result_context, expected_context)
        self.assertTrue(polarity)

    def test_complex_implication_nnf(self) -> None:
        """Test NNF conversion for nested implication contexts."""
        context = ctx.Not(
            ctx.Not(
                ctx.ImpliesLeft(
                    ctx.Eventually(ctx.Not(ctx.Hole()), (1, 5)),
                    mtl.Always(mtl.Prop("r")),
                ),
            ),
        )
        expected_context = ctx.OrLeft(
            ctx.Always(ctx.Hole(), (1, 5)),
            mtl.Always(mtl.Prop("r")),
        )
        result_context, polarity = ctx.partial_nnf_ctx(context)
        self.assertEqual(result_context, expected_context)
        self.assertTrue(polarity)

    def test_complex_temporal_operators_nnf(self) -> None:
        """Test NNF conversion for complex temporal operator combinations."""
        context = ctx.Not(
            ctx.Eventually(
                ctx.AndLeft(
                    ctx.Always(ctx.Hole(), (2, 8)),
                    mtl.Eventually(mtl.Prop("s"), (0, 3)),
                ),
                (0, None),
            ),
        )
        expected_context = ctx.Always(
            ctx.OrLeft(
                ctx.Eventually(ctx.Hole(), (2, 8)),
                mtl.Not(mtl.Eventually(mtl.Prop("s"), (0, 3))),
            ),
            (0, None),
        )
        result_context, polarity = ctx.partial_nnf_ctx(context)
        self.assertEqual(result_context, expected_context)
        self.assertFalse(polarity)


class TestPartialNNF(unittest.TestCase):
    def test_pnnf_subformula(self) -> None:
        context = ctx.Not(ctx.Hole())
        subformula = parser.parse_mtl("G[1,5] a")
        assert isinstance(subformula, mtl.Temporal)
        expected_subformula = parser.parse_mtl("F[1,5] !a")
        result_context, result_subformula = ctx.partial_nnf(context, subformula)
        self.assertEqual(result_subformula, expected_subformula)
        self.assertEqual(result_context, ctx.Hole())


if __name__ == "__main__":
    unittest.main()
