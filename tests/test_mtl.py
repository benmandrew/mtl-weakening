import unittest

from src import ltl as l
from src import mtl as m


class TestMtlToLtl(unittest.TestCase):

    def test_eventually_upper_bound(self):
        mtl = m.Eventually(m.Prop("p"), (2, 4))
        expected = l.Next(
            l.Next(
                l.Or(
                    l.Prop("p"), l.Next(l.Or(l.Prop("p"), l.Next(l.Prop("p"))))
                )
            )
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_eventually_infinite_upper_bound(self):
        mtl = m.Eventually(m.Prop("p"), (1, None))
        expected = l.Next(l.Eventually(l.Prop("p")))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_upper_bound(self):
        mtl = m.Always(m.Prop("p"), (1, 3))
        expected = l.Next(
            l.And(l.Prop("p"), l.Next(l.And(l.Prop("p"), l.Next(l.Prop("p")))))
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_infinite_upper_bound(self):
        mtl = m.Always(m.Prop("p"), (3, None))
        expected = l.Next(l.Next(l.Next(l.Always(l.Prop("p")))))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_upper_bound(self):
        mtl = m.Until(m.Prop("p"), m.Prop("q"), (1, 2))
        expected = l.Next(
            l.Or(l.Prop("q"), l.And(l.Prop("p"), l.Next(l.Prop("q"))))
        )
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_infinite_upper_bound(self):
        mtl = m.Until(m.Prop("p"), m.Prop("q"), (2, None))
        expected = l.Next(l.Next(l.Until(l.Prop("p"), l.Prop("q"))))
        result = m.mtl_to_ltl(mtl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))


class TestMtlToString(unittest.TestCase):
    def test_deep_nested_negations_and_temporal(self):
        formula = m.Not(
            m.Implies(
                m.And(m.Prop("p"), m.Not(m.Eventually(m.Prop("q"), (1, 2)))),
                m.Always(m.Or(m.Not(m.Prop("r")), m.Next(m.Prop("s"))), (0, 3)),
            )
        )
        self.assertEqual(
            m.to_string(formula),
            "!(((p & !(F[1, 2] (q))) -> G[0, 3] ((!(r) | X (s)))))",
        )

    def test_complex_mixed_with_next_and_implies(self):
        formula = m.And(
            m.Implies(m.Prop("p"), m.Next(m.Eventually(m.Prop("q"), (2, 4)))),
            m.Not(m.Or(m.Prop("r"), m.Until(m.Prop("s"), m.Prop("t"), (1, 3)))),
        )
        self.assertEqual(
            m.to_string(formula),
            "((p -> X (F[2, 4] (q))) & !((r | (s U[1, 3] t))))",
        )


if __name__ == "__main__":
    unittest.main()
