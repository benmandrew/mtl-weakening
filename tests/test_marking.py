import unittest

from src import marking, util
from src.logic import mtl


class TestTrace(unittest.TestCase):
    def test_trace_idx(self) -> None:
        trace = marking.Trace(
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
        trace = marking.Trace(
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
        expected = util.format_expect(
            """
                                   0 1 2 3 4 5 6
            G (F[0, 4] (trigger)) │ │ │ │ │ │ │ │
            F[0, 4] (trigger)     │ │ │●│●│●│●│●│
            trigger               │ │ │ │ │ │ │●│
            =Lasso=                  └─────────┘
        """,
        )
        result = util.format_expect(str(marking.Marking(trace, formula)))
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
        expected = util.format_expect(
            """
                             0 1 2 3 4
            G (F[0, 4] (a)) │●│●│●│●│●│
            F[0, 4] (a)     │●│●│●│●│●│
            a               │ │ │ │ │●│
            =Lasso=          └───────┘
        """,
        )
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_f(self) -> None:
        formula = mtl.Eventually(mtl.Or(mtl.Prop("a"), mtl.Prop("b")))
        trace = marking.Trace(
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_gfg(self) -> None:
        formula = mtl.Always(
            mtl.Eventually(mtl.Always(mtl.Prop("a"), (0, 2)), (0, 4)),
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_fg(self) -> None:
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
        formula = mtl.Eventually(
            mtl.Until(mtl.Prop("p"), mtl.Prop("q"), (1, 2)),
            (0, 2),
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_ngu(self) -> None:
        formula = mtl.Not(
            mtl.Always(mtl.Until(mtl.Prop("p"), mtl.Prop("q"), (1, 3)), (0, 3)),
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_r(self) -> None:
        formula = mtl.Release(mtl.Prop("b"), mtl.Prop("a"), (0, 2))
        trace = marking.Trace(
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)
        trace = marking.Trace(
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_ugf(self) -> None:
        formula = mtl.Until(
            mtl.Always(mtl.Eventually(mtl.Prop("b"), (0, 1))),
            mtl.Prop("a"),
        )
        trace = marking.Trace(
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
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
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_long_bool(self) -> None:
        formula = mtl.Or(mtl.TrueBool(), mtl.Prop("a"))
        trace = marking.Trace(
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
        (true | a) │●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│●│
        a          │●│ │ │ │ │ │ │ │●│ │ │ │ │ │ │●│ │ │ │ │ │ │ │●│●│ │ │ │ │ │ │ │●│
        =Lasso=                                             └───────────────────────┘
        """,
        )
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)
        formula = mtl.Or(mtl.FalseBool(), mtl.Prop("a"))
        expected = util.format_expect(
            """
                                         1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 3 3 3
                     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
        (false | a) │●│ │ │ │ │ │ │ │●│ │ │ │ │ │ │●│ │ │ │ │ │ │ │●│●│ │ │ │ │ │ │ │●│
        a           │●│ │ │ │ │ │ │ │●│ │ │ │ │ │ │●│ │ │ │ │ │ │ │●│●│ │ │ │ │ │ │ │●│
        =Lasso=                                              └───────────────────────┘
        """,
        )
        result = util.format_expect(str(marking.Marking(trace, formula)))
        self.assertEqual(result, expected)

    def test_fmt_markings_timer(self) -> None:
        trace = marking.Trace(
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
            marking.markings_to_str(trace.to_markings(), None),
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
            marking.markings_to_str(trace.to_markings(), trace.loop_start),
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
