import unittest

import lark

from src.logic import mtl, parser


class TestParseMtl(unittest.TestCase):
    def test_parse_always(self) -> None:
        formula = parser.parse_mtl("G[0,2] (phi & psi)")
        expected = mtl.Always(mtl.And(mtl.Prop("phi"), mtl.Prop("psi")), (0, 2))
        self.assertEqual(formula, expected)

    def test_parse_until_associative(self) -> None:
        formula = parser.parse_mtl("a U[20, 30] b U[0, 1] c")
        expected = mtl.Until(
            mtl.Until(mtl.Prop("a"), mtl.Prop("b"), (20, 30)),
            mtl.Prop("c"),
            (0, 1),
        )
        self.assertEqual(formula, expected)

    def test_parse_until_without_interval(self) -> None:
        formula = parser.parse_mtl("a U b")
        expected = mtl.Until(
            mtl.Prop("a"),
            mtl.Prop("b"),
            (0, None),
        )
        self.assertEqual(formula, expected)

    def test_parse_release(self) -> None:
        formula = parser.parse_mtl("a R[0,2] b")
        expected = mtl.Release(mtl.Prop("a"), mtl.Prop("b"), (0, 2))
        self.assertEqual(formula, expected)

    def test_parse_temporal_precedence(self) -> None:
        formula = parser.parse_mtl("a U F[2,3] b")
        expected: mtl.Mtl = mtl.Until(
            mtl.Prop("a"),
            mtl.Eventually(mtl.Prop("b"), (2, 3)),
        )
        self.assertEqual(formula, expected)
        formula = parser.parse_mtl("F[0,1] b U a")
        expected = mtl.Until(
            mtl.Eventually(mtl.Prop("b"), (0, 1)),
            mtl.Prop("a"),
        )
        self.assertEqual(formula, expected)
        formula = parser.parse_mtl("G (a U G[1,4] b)")
        expected = mtl.Always(
            mtl.Until(mtl.Prop("a"), mtl.Always(mtl.Prop("b"), (1, 4))),
        )
        self.assertEqual(formula, expected)

    def test_parse_infinity(self) -> None:
        formula = parser.parse_mtl("F (F[5,∞] (phi -> psi))")
        expected = mtl.Eventually(
            mtl.Eventually(
                mtl.Implies(mtl.Prop("phi"), mtl.Prop("psi")),
                (5, None),
            ),
            (0, None),
        )
        self.assertEqual(formula, expected)

    def test_parse_invalid_formula(self) -> None:
        formula = "G (phi"
        with self.assertRaises(lark.UnexpectedToken):
            parser.parse_mtl(formula)
