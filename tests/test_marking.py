import unittest
import textwrap
from src import marking
from src import mitl


def format_expect(s: str) -> str:
    return textwrap.dedent(s).strip("\n")


class TestMarking(unittest.TestCase):

    def setUp(self):
        super(TestMarking, self).setUp()
        self.addTypeEqualityFunc(str, self.assertMultiLineEqual)

    def test_fmt_markings_1(self):
        formula = mitl.Always(mitl.Eventually(mitl.Prop("trigger"), (0, 4)))
        trace = marking.Trace(
            [
                {"counter": 0, "trigger": False},
                {"counter": 1, "trigger": False},
                {"counter": 2, "trigger": False},
                {"counter": 3, "trigger": False},
                {"counter": 4, "trigger": False},
                {"counter": 5, "trigger": False},
                {"counter": 0, "trigger": True},
            ],
            1,
        )
        expected = format_expect(
            """
            trigger               :  - - - - - -X
            F[0, 4] (trigger)     :  - -X-X-X-X-X
            G (F[0, 4] (trigger)) :  - - - - - - 
        """
        )
        result = marking.fmt_markings(marking.mark_trace(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_2(self):
        formula = mitl.Eventually(mitl.Or(mitl.Prop("a"), mitl.Prop("b")))
        trace = marking.Trace(
            [
                {"a": True, "b": False},
                {"a": False, "b": True},
            ],
            0,
        )
        expected = format_expect(
            """
            b           :  -X
            a           : X- 
            (a | b)     : X-X
            F ((a | b)) : X-X
        """
        )
        result = marking.fmt_markings(marking.mark_trace(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_3(self):
        formula = mitl.Always(
            mitl.Eventually(mitl.Always(mitl.Prop("a"), (0, 2)), (0, 4))
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
            a                         : X-X-X- - -X-X- - -X
            G[0, 2] (a)               : X- - - - - - - - -X
            F[0, 4] (G[0, 2] (a))     : X- - - - -X-X-X-X-X
            G (F[0, 4] (G[0, 2] (a))) :  - - - - -X-X-X-X-X
        """
        )
        result = marking.fmt_markings(marking.mark_trace(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_4(self):
        formula = mitl.Always(mitl.Eventually(mitl.Prop("a"), (0, 4)))
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
            a               :  - - - -X
            F[0, 4] (a)     : X-X-X-X-X
            G (F[0, 4] (a)) : X-X-X-X-X
        """
        )
        result = marking.fmt_markings(marking.mark_trace(trace, formula))
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
