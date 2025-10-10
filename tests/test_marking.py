import unittest

from src import util
from src.logic import mtl, parser
from src.marking import common, lasso


class TestTrace(unittest.TestCase):
    def test_trace_idx(self) -> None:
        trace = common.Trace(
            [
                {"a": True},
                {"a": True},
                {"a": True},
                {"a": True},
            ],
            2,
        )
        self.assertEqual(trace.idx(0), 0)
        self.assertEqual(trace.idx(1), 1)
        self.assertEqual(trace.idx(2), 2)
        self.assertEqual(trace.idx(3), 3)
        self.assertEqual(trace.idx(4), 2)
        self.assertEqual(trace.idx(5), 3)
        self.assertEqual(trace.idx(6), 2)

    def test_trace_right_idx(self) -> None:
        trace = common.Trace(
            [
                {"a": True},
                {"a": True},
                {"a": True},
                {"a": True},
                {"a": True},
            ],
            2,
        )
        self.assertEqual(trace.idx(trace.right_idx(0)), 4)
        self.assertEqual(trace.idx(trace.right_idx(1)), 4)
        self.assertEqual(trace.idx(trace.right_idx(2)), 4)
        self.assertEqual(trace.idx(trace.right_idx(3)), 2)
        self.assertEqual(trace.idx(trace.right_idx(4)), 3)
        self.assertEqual(trace.idx(trace.right_idx(5)), 4)
        self.assertEqual(trace.idx(trace.right_idx(6)), 2)


class TestMarkingLasso(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.addTypeEqualityFunc(str, self.assertMultiLineEqual)

    def test_fmt_markings_gf(self) -> None:
        formula = parser.parse_mtl("G (F[0, 4] (trigger))")
        trace = common.Trace(
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
        expected = util.format_expect(
            """
                                   0 1 2 3 4 5 6
            G (F[0, 4] (trigger)) │ │ │ │ │ │ │ │
            F[0, 4] (trigger)     │ │ │●│●│●│●│●│
            trigger               │ │ │ │ │ │ │●│
            =Lasso=                  └─────────┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)
        formula = parser.parse_mtl("G (F[0, 4] (a))")
        trace = common.Trace(
            [
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            0,
        )
        expected = util.format_expect(
            """
                             0 1 2 3 4
            G (F[0, 4] (a)) │●│●│●│●│●│
            F[0, 4] (a)     │●│●│●│●│●│
            a               │ │ │ │ │●│
            =Lasso=          └───────┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_f(self) -> None:
        formula = parser.parse_mtl("F ((a | b))")
        trace = common.Trace(
            [
                {"a": True, "b": False},
                {"a": False, "b": True},
            ],
            0,
        )
        expected = util.format_expect(
            """
                         0 1
            F ((a | b)) │●│●│
            (a | b)     │●│●│
            b           │ │●│
            a           │●│ │
            =Lasso=      └─┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_gfg(self) -> None:
        formula = parser.parse_mtl("G (F[0, 4] (G[0, 2] (a)))")
        trace = common.Trace(
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
        expected = util.format_expect(
            """
                                       0 1 2 3 4 5 6 7 8 9
            G (F[0, 4] (G[0, 2] (a))) │ │ │ │ │ │●│●│●│●│●│
            F[0, 4] (G[0, 2] (a))     │●│ │ │ │ │●│●│●│●│●│
            G[0, 2] (a)               │●│ │ │ │ │ │ │ │ │●│
            a                         │●│●│●│ │ │●│●│ │ │●│
            =Lasso=                                      ⊔
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)
        trace = common.Trace(
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
        expected = util.format_expect(
            """
                                       0 1 2 3 4 5 6 7 8 9
            G (F[0, 4] (G[0, 2] (a))) │●│●│●│●│●│●│●│●│●│●│
            F[0, 4] (G[0, 2] (a))     │●│●│●│●│●│●│●│●│●│●│
            G[0, 2] (a)               │●│ │ │ │●│ │ │ │ │●│
            a                         │●│●│●│ │●│●│●│ │ │●│
            =Lasso=                                      ⊔
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)
        formula = parser.parse_mtl("G (F (G[2, 5] (a)))")
        trace = common.Trace(
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
        expected = util.format_expect(
            """
                                 0 1 2 3 4 5 6
            G (F (G[2, 5] (a))) │ │ │ │ │ │ │ │
            F (G[2, 5] (a))     │ │ │ │ │ │ │ │
            G[2, 5] (a)         │ │ │ │ │ │ │ │
            a                   │ │●│●│ │ │ │●│
            =Lasso=                  └───────┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_fg(self) -> None:
        formula = parser.parse_mtl("F (G[0, 1] (a))")
        trace = common.Trace(
            [
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
                {"a": True},
            ],
            0,
        )
        markings = lasso.Marking(trace, formula)
        formula = parser.parse_mtl("F (G[0, 2] (a))")
        expected = util.format_expect(
            """
                             0 1 2 3 4
            F (G[0, 2] (a)) │ │ │ │ │ │
            G[0, 2] (a)     │ │ │ │ │ │
            F (G[0, 1] (a)) │●│●│●│●│●│
            G[0, 1] (a)     │ │ │ │●│ │
            a               │ │ │ │●│●│
            =Lasso=          └───────┘
        """,
        )
        markings[formula]  # pylint: disable=pointless-statement
        self.assertEqual(util.format_expect(str(markings)), expected)

    def test_fmt_markings_fu(self) -> None:
        formula = parser.parse_mtl("F[0, 2] ((p U[1, 2] q))")
        trace = common.Trace(
            [
                {"p": True, "q": False},
                {"p": True, "q": False},
                {"p": True, "q": True},
                {"p": False, "q": False},
            ],
            0,
        )
        expected = util.format_expect(
            """
                                     0 1 2 3
            F[0, 2] ((p U[1, 2] q)) │●│●│●│●│
            (p U[1, 2] q)           │●│●│ │ │
            q                       │ │ │●│ │
            p                       │●│●│●│ │
            =Lasso=                  └─────┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_ngu(self) -> None:
        formula = parser.parse_mtl("!G[0, 3] ((p U[1, 3] q))")
        trace = common.Trace(
            [
                {"p": True, "q": False},
                {"p": True, "q": False},
                {"p": True, "q": True},
                {"p": True, "q": False},
                {"p": False, "q": False},
            ],
            0,
        )
        expected = util.format_expect(
            """
                                        0 1 2 3 4
            !(G[0, 3] ((p U[1, 3] q))) │●│●│●│●│●│
            G[0, 3] ((p U[1, 3] q))    │ │ │ │ │ │
            (p U[1, 3] q)              │●│●│ │ │●│
            q                          │ │ │●│ │ │
            p                          │●│●│●│●│ │
            =Lasso=                     └───────┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_r(self) -> None:
        formula = parser.parse_mtl("(b R[0, 2] a)")
        trace = common.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": False},
                {"a": False, "b": False},
            ],
            0,
        )
        expected = util.format_expect(
            """
                           0 1 2
            (b R[0, 2] a) │ │ │ │
            b             │ │ │ │
            a             │●│●│ │
            =Lasso=        └───┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)
        trace = common.Trace(
            [
                {"a": True, "b": False},
                {"a": True, "b": True},
                {"a": False, "b": False},
            ],
            0,
        )
        expected = util.format_expect(
            """
                           0 1 2
            (b R[0, 2] a) │●│●│ │
            b             │ │●│ │
            a             │●│●│ │
            =Lasso=        └───┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_ugf(self) -> None:
        formula = parser.parse_mtl("(G (F[0, 1] (b)) U a)")
        trace = common.Trace(
            [
                {"a": False, "b": False},
                {"a": False, "b": True},
                {"a": False, "b": False},
                {"a": False, "b": True},
                {"a": True, "b": False},
            ],
            4,
        )
        expected = util.format_expect(
            """
                               0 1 2 3 4
        (G (F[0, 1] (b)) U a) │ │ │ │ │●│
        G (F[0, 1] (b))       │ │ │ │ │ │
        F[0, 1] (b)           │●│●│●│●│ │
        b                     │ │●│ │●│ │
        a                     │ │ │ │ │●│
        =Lasso=                        ⊔
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)
        formula = mtl.Until(
            mtl.Eventually(mtl.Prop("b"), (0, 1)),
            mtl.Prop("a"),
        )
        expected = util.format_expect(
            """
                           0 1 2 3 4
        (F[0, 1] (b) U a) │●│●│●│●│●│
        F[0, 1] (b)       │●│●│●│●│ │
        b                 │ │●│ │●│ │
        a                 │ │ │ │ │●│
        =Lasso=                    ⊔
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_long_bool(self) -> None:
        formula = parser.parse_mtl("(TRUE | a)")
        trace = common.Trace(
            [
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
                {"a": True},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": False},
                {"a": True},
            ],
            20,
        )
        expected = util.format_expect(
            """
                                        1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 3 3 3
                    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
        (TRUE | a) │●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│
        a          │●│ │ │ │ │ │ │ │●│ │ │ │ │ │ │●│ │ │ │ │ │ │ │●│●│ │ │ │ │ │ │ │●│
        =Lasso=                                             └───────────────────────┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)
        formula = parser.parse_mtl("(FALSE | a)")
        expected = util.format_expect(
            """
                                         1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 3 3 3
                     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
        (FALSE | a) │●│ │ │ │ │ │ │ │●│ │ │ │ │ │ │●│ │ │ │ │ │ │ │●│●│ │ │ │ │ │ │ │●│
        a           │●│ │ │ │ │ │ │ │●│ │ │ │ │ │ │●│ │ │ │ │ │ │ │●│●│ │ │ │ │ │ │ │●│
        =Lasso=                                              └───────────────────────┘
        """,
        )
        result = util.format_expect(str(lasso.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_timer(self) -> None:
        trace = common.Trace(
            [
                {"a": False, "b": False, "timer": 2},
                {"a": False, "b": True, "timer": 1},
                {"a": False, "b": False, "timer": 2},
                {"a": False, "b": True, "timer": 5},
                {"a": True, "b": False, "timer": 100},
            ],
            1,
        )
        expected = util.format_expect(
            """
               0 1 2 3 4
        timer │2│1│2│5│*│
        b     │ │●│ │●│ │
        a     │ │ │ │ │●│
        """,
        )
        result = util.format_expect(
            common.markings_to_str(trace.to_markings(), None),
        )
        self.assertEqual(result, expected)
        expected = util.format_expect(
            """
                 0 1 2 3 4
        timer   │2│1│2│5│*│
        b       │ │●│ │●│ │
        a       │ │ │ │ │●│
        =Lasso=    └─────┘
        """,
        )
        result = util.format_expect(
            common.markings_to_str(trace.to_markings(), trace.loop_start),
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
