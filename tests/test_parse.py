import unittest

import lark

from src.logic import mtl, parser


class TestParseMtl(unittest.TestCase):
    def test_parse_always(self) -> None:
        formula = "G[0,2] (phi & psi)"
        expected = mtl.Always(mtl.And(mtl.Prop("phi"), mtl.Prop("psi")), (0, 2))
        self.assertEqual(parser.parse_mtl(formula), expected)

    def test_parse_until(self) -> None:
        formula = "a U[20, 30] b U[0, 1] c"
        expected = mtl.Until(
            mtl.Until(mtl.Prop("a"), mtl.Prop("b"), (20, 30)),
            mtl.Prop("c"),
            (0, 1),
        )
        self.assertEqual(parser.parse_mtl(formula), expected)

    def test_parse_infinity(self) -> None:
        formula = "F (F[5,∞] (phi -> psi))"
        expected = mtl.Eventually(
            mtl.Eventually(
                mtl.Implies(mtl.Prop("phi"), mtl.Prop("psi")),
                (5, None),
            ),
            (0, None),
        )
        self.assertEqual(parser.parse_mtl(formula), expected)

    def test_parse_invalid_formula(self) -> None:
        formula = "G (phi"
        with self.assertRaises(lark.UnexpectedToken):
            parser.parse_mtl(formula)
