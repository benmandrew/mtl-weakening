import unittest

from src.logic import ltl as l
from src.logic import mtl as m


class TestMtlToLtl(unittest.TestCase):

    def test_eventually_upper_bound(self) -> None:
        mtl = m.Eventually(m.Prop("p"), (2, 4))
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
        mtl = m.Eventually(m.Prop("p"), (1, None))
        expected = l.Next(l.Eventually(l.Prop("p")))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_upper_bound(self) -> None:
        mtl = m.Always(m.Prop("p"), (1, 3))
        expected = l.Next(
            l.And(l.Prop("p"), l.Next(l.And(l.Prop("p"), l.Next(l.Prop("p"))))),
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_infinite_upper_bound(self) -> None:
        mtl = m.Always(m.Prop("p"), (3, None))
        expected = l.Next(l.Next(l.Next(l.Always(l.Prop("p")))))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_upper_bound(self) -> None:
        mtl = m.Until(m.Prop("p"), m.Prop("q"), (1, 2))
        expected = l.Next(
            l.Or(l.Prop("q"), l.And(l.Prop("p"), l.Next(l.Prop("q")))),
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_infinite_upper_bound(self) -> None:
        mtl = m.Until(m.Prop("p"), m.Prop("q"), (2, None))
        expected = l.Next(l.Next(l.Until(l.Prop("p"), l.Prop("q"))))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_boolean(self) -> None:
        mtl = m.And(m.TrueBool(), m.FalseBool())
        expected = l.And(l.TrueBool(), l.FalseBool())
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))


class TestMtlToString(unittest.TestCase):
    def test_deep_nested_negations_and_temporal(self) -> None:
        formula = m.Not(
            m.Implies(
                m.And(m.Prop("p"), m.Not(m.Eventually(m.Prop("q"), (1, 2)))),
                m.Always(
                    m.Or(m.Not(m.Prop("r")), m.Next(m.TrueBool())),
                    (0, 3),
                ),
            ),
        )
        self.assertEqual(
            m.to_string(formula),
            "!(((p & !(F[1, 2] (q))) -> G[0, 3] ((!(r) | X (true)))))",
        )

    def test_complex_mixed_with_next_and_implies(self) -> None:
        formula = m.And(
            m.Implies(m.FalseBool(), m.Next(m.Eventually(m.Prop("q"), (2, 4)))),
            m.Not(m.Or(m.Prop("r"), m.Until(m.Prop("s"), m.Prop("t"), (1, 3)))),
        )
        self.assertEqual(
            m.to_string(formula),
            "((false -> X (F[2, 4] (q))) & !((r | (s U[1, 3] t))))",
        )


if __name__ == "__main__":
    unittest.main()
