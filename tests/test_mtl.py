import unittest

from src.logic import ltl as l
from src.logic import mtl as m
from src.logic import parser


class TestMtlToLtl(unittest.TestCase):

    def test_eventually_upper_bound(self) -> None:
        mtl = parser.parse_mtl("F[2,4] p")
        expected = l.Next(
            l.Next(
                l.Or(
                    l.Prop("p"),
                    l.Next(l.Or(l.Prop("p"), l.Next(l.Prop("p")))),
                ),
            ),
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_eventually_infinite_upper_bound(self) -> None:
        mtl = parser.parse_mtl("F[1,∞] p")
        expected = l.Next(l.Eventually(l.Prop("p")))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_upper_bound(self) -> None:
        mtl = parser.parse_mtl("G[1,3] p")
        expected = l.Next(
            l.And(l.Prop("p"), l.Next(l.And(l.Prop("p"), l.Next(l.Prop("p"))))),
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_infinite_upper_bound(self) -> None:
        mtl = parser.parse_mtl("G[3,∞] p")
        expected = l.Next(l.Next(l.Next(l.Always(l.Prop("p")))))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_upper_bound(self) -> None:
        mtl = parser.parse_mtl("p U[1,2] q")
        expected = l.Next(
            l.Or(l.Prop("q"), l.And(l.Prop("p"), l.Next(l.Prop("q")))),
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_infinite_upper_bound(self) -> None:
        mtl = parser.parse_mtl("p U[2,∞] q")
        expected = l.Next(l.Next(l.Until(l.Prop("p"), l.Prop("q"))))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_release_upper_bound(self) -> None:
        mtl = parser.parse_mtl("p R[1,2] q")
        expected = l.Next(
            l.Or(
                l.Or(
                    l.And(l.Prop("q"), l.Next(l.Prop("q"))),
                    l.And(l.Prop("p"), l.Prop("q")),
                ),
                l.And(l.Prop("q"), l.Next(l.And(l.Prop("p"), l.Prop("q")))),
            ),
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_release_infinite_upper_bound(self) -> None:
        mtl = parser.parse_mtl("p R[2,∞] q")
        expected: l.Ltl
        expected = l.Next(l.Next(l.Release(l.Prop("p"), l.Prop("q"))))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))
        mtl = parser.parse_mtl("p R q")
        expected = l.Release(l.Prop("p"), l.Prop("q"))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_boolean(self) -> None:
        mtl = parser.parse_mtl("TRUE & FALSE")
        expected = l.And(l.TrueBool(), l.FalseBool())
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))


class TestMtlToString(unittest.TestCase):
    def test_deep_nested_negations_and_temporal(self) -> None:
        formula = parser.parse_mtl(
            "!(((p & !(F[1, 2] (q))) -> G[0, 3] ((!(r) | X (TRUE)))))",
        )
        self.assertEqual(
            m.to_string(formula),
            "!(((p & !(F[1, 2] (q))) -> G[0, 3] ((!(r) | X (TRUE)))))",
        )

    def test_complex_mixed_with_next_and_implies(self) -> None:
        formula = m.And(
            m.Implies(m.FalseBool(), m.Next(m.Eventually(m.Prop("q"), (2, 4)))),
            m.Not(m.Or(m.Prop("r"), m.Until(m.Prop("s"), m.Prop("t"), (1, 3)))),
        )
        self.assertEqual(
            m.to_string(formula),
            "((FALSE -> X (F[2, 4] (q))) & !((r | (s U[1, 3] t))))",
        )


if __name__ == "__main__":
    unittest.main()
