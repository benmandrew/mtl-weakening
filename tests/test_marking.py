import unittest
from src import marking
from src import mitl


class TestMarking(unittest.TestCase):

    def setUp(self):
        super(TestMarking, self).setUp()
        self.addTypeEqualityFunc(str, self.assertMultiLineEqual)

    def test_fmt_markings_1(self):
        formula = mitl.Always(mitl.Eventually(mitl.Prop("trigger"), (0, 4)))
        trace = [
            {"counter": 0, "trigger": False},
            {"counter": 1, "trigger": False},
            {"counter": 2, "trigger": False},
            {"counter": 3, "trigger": False},
            {"counter": 4, "trigger": False},
            {"counter": 5, "trigger": False},
            {"counter": 0, "trigger": True},
            {"counter": 1, "trigger": False},
        ]
        expected = """trigger                     :  - - - - - -X- 
F[0, 4] (trigger)           :  - -X-X-X-X-X- 
G[0, ∞) (F[0, 4] (trigger)) :  - - - - - - - """
        result = marking.fmt_markings(marking.mark_trace(trace, formula))
        self.assertEqual(result, expected)

    def test_fmt_markings_2(self):
        formula = mitl.Eventually(mitl.Or(mitl.Prop("a"), mitl.Prop("b")))
        trace: list[dict[str, bool | int]] = [
            {"a": True, "b": False},
            {"a": False, "b": True},
            {"a": True, "b": False},
        ]
        expected = """b                 :  -X- 
a                 : X- -X
(a | b)           : X-X-X
F[0, ∞) ((a | b)) : X-X-X"""
        result = marking.fmt_markings(marking.mark_trace(trace, formula))
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
