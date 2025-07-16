import unittest
import mitl as m
import ltl as l


class TestMitlToLtl(unittest.TestCase):

    def test_eventually_upper_bound(self):
        mitl = m.Eventually(m.Prop("p"), (2, 4))
        expected = l.Next(
            l.Next(
                l.Or(
                    l.Prop("p"), l.Next(l.Or(l.Prop("p"), l.Next(l.Prop("p"))))
                )
            )
        )
        result = m.mitl_to_ltl(mitl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_eventually_infinite_upper_bound(self):
        mitl = m.Eventually(m.Prop("p"), (1, None))
        expected = l.Next(l.Eventually(l.Prop("p")))
        result = m.mitl_to_ltl(mitl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_upper_bound(self):
        mitl = m.Always(m.Prop("p"), (1, 3))
        expected = l.Next(
            l.And(l.Prop("p"), l.Next(l.And(l.Prop("p"), l.Next(l.Prop("p")))))
        )
        result = m.mitl_to_ltl(mitl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_always_infinite_upper_bound(self):
        mitl = m.Always(m.Prop("p"), (3, None))
        expected = l.Next(l.Next(l.Next(l.Always(l.Prop("p")))))
        result = m.mitl_to_ltl(mitl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_upper_bound(self):
        mitl = m.Until(m.Prop("p"), m.Prop("q"), (1, 2))
        expected = l.Next(
            l.Or(l.Prop("q"), l.And(l.Prop("p"), l.Next(l.Prop("q"))))
        )
        result = m.mitl_to_ltl(mitl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))

    def test_until_infinite_upper_bound(self):
        mitl = m.Until(m.Prop("p"), m.Prop("q"), (2, None))
        expected = l.Next(l.Next(l.Until(l.Prop("p"), l.Prop("q"))))
        result = m.mitl_to_ltl(mitl)
        self.assertEqual(l.to_nuxmv(result), l.to_nuxmv(expected))


if __name__ == "__main__":
    unittest.main()
