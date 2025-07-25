import textwrap
import unittest

from src import marking
from src.logic import mtl


def format_expect(s: str) -> str:
    return textwrap.dedent(s).strip("\n")


class TestMarking(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.addTypeEqualityFunc(str, self.assertMultiLineEqual)

    def test_fmt_markings_gf(self):
        formula = mtl.Always(mtl.Eventually(mtl.Prop("trigger"), (0, 4)))
        trace = marking.Trace(
            [
                {"trigger": False},
                {"trigger": False},
                {"trigger": False},
                {"trigger": False},
                {"trigger": False},
                {"trigger": False},
                {"trigger": True},
            ],
            1,
        )
        expected = format_expect(
            """
            G (F[0, 4] (trigger)) │ │ │ │ │ │ │ │
            F[0, 4] (trigger)     │ │ │●│●│●│●│●│
            trigger               │ │ │ │ │ │ │●│
            =Lasso=                  └─────────┘
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)
        formula = mtl.Always(mtl.Eventually(mtl.Prop("a"), (0, 4)))
        trace = marking.Trace(
            [
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            0,
        )
        expected = format_expect(
            """
            G (F[0, 4] (a)) │●│●│●│●│●│
            F[0, 4] (a)     │●│●│●│●│●│
            a               │ │ │ │ │●│
            =Lasso=          └───────┘
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_f(self):
        formula = mtl.Eventually(mtl.Or(mtl.Prop("a"), mtl.Prop("b")))
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": False, "b": True},
            ],
            0,
        )
        expected = format_expect(
            """
            F ((a | b)) │●│●│
            (a | b)     │●│●│
            b           │ │●│
            a           │●│ │
            =Lasso=      └─┘
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_gfg(self):
        formula = mtl.Always(
            mtl.Eventually(mtl.Always(mtl.Prop("a"), (0, 2)), (0, 4))
        )
        trace = marking.Trace(
            [
                {"a": True},
                {"a": True},
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": True},
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            9,
        )
        expected = format_expect(
            """
            G (F[0, 4] (G[0, 2] (a))) │ │ │ │ │ │●│●│●│●│●│
            F[0, 4] (G[0, 2] (a))     │●│ │ │ │ │●│●│●│●│●│
            G[0, 2] (a)               │●│ │ │ │ │ │ │ │ │●│
            a                         │●│●│●│ │ │●│●│ │ │●│
            =Lasso=                                      ⊔
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)
        trace = marking.Trace(
            [
                {"a": True},
                {"a": True},
                {"a": True},
                {"a": False},
                {"a": True},
                {"a": True},
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            9,
        )
        expected = format_expect(
            """
            G (F[0, 4] (G[0, 2] (a))) │●│●│●│●│●│●│●│●│●│●│
            F[0, 4] (G[0, 2] (a))     │●│●│●│●│●│●│●│●│●│●│
            G[0, 2] (a)               │●│ │ │ │●│ │ │ │ │●│
            a                         │●│●│●│ │●│●│●│ │ │●│
            =Lasso=                                      ⊔
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)
        formula = mtl.Always(mtl.Eventually(mtl.Always(mtl.Prop("a"), (2, 5))))
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
        expected = format_expect(
            """
            G (F (G[2, 5] (a))) │ │ │ │ │ │ │ │
            F (G[2, 5] (a))     │ │ │ │ │ │ │ │
            G[2, 5] (a)         │ │ │ │ │ │ │ │
            a                   │ │●│●│ │ │ │●│
            =Lasso=                  └───────┘
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_fg(self):
        formula = mtl.Eventually(mtl.Always(mtl.Prop("a"), (0, 1)))
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
        markings = marking.Marking(trace, formula)
        formula = mtl.Eventually(mtl.Always(mtl.Prop("a"), (0, 2)))
        expected = format_expect(
            """
            F (G[0, 2] (a)) │ │ │ │ │ │
            G[0, 2] (a)     │ │ │ │ │ │
            F (G[0, 1] (a)) │●│●│●│●│●│
            G[0, 1] (a)     │ │ │ │●│ │
            a               │ │ │ │●│●│
            =Lasso=          └───────┘
        """
        )
        markings[formula]
        self.assertEqual(str(markings), expected)

    def test_fmt_markings_fu(self):
        formula = mtl.Eventually(
            mtl.Until(mtl.Prop("p"), mtl.Prop("q"), (1, 2)), (0, 2)
        )
        trace = marking.Trace(
            [
                {"p": True, "q": False},
                {"p": True, "q": False},
                {"p": True, "q": True},
                {"p": False, "q": False},
            ],
            0,
        )
        expected = format_expect(
            """
            F[0, 2] ((p U[1, 2] q)) │●│●│●│●│
            (p U[1, 2] q)           │●│●│ │ │
            q                       │ │ │●│ │
            p                       │●│●│●│ │
            =Lasso=                  └─────┘
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_ngu(self):
        formula = mtl.Not(
            mtl.Always(mtl.Until(mtl.Prop("p"), mtl.Prop("q"), (1, 3)), (0, 3))
        )
        trace = marking.Trace(
            [
                {"p": True, "q": False},
                {"p": True, "q": False},
                {"p": True, "q": True},
                {"p": True, "q": False},
                {"p": False, "q": False},
            ],
            0,
        )
        expected = format_expect(
            """
            !(G[0, 3] ((p U[1, 3] q))) │●│●│●│●│●│
            G[0, 3] ((p U[1, 3] q))    │ │ │ │ │ │
            (p U[1, 3] q)              │●│●│ │ │●│
            q                          │ │ │●│ │ │
            p                          │●│●│●│●│ │
            =Lasso=                     └───────┘
        """
        )
        result = str(marking.Marking(trace, formula))
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
