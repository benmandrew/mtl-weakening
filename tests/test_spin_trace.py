import pathlib
import unittest

from src import util
from src.marking import common
from src.trace_analysis import exceptions, spin_trace


def read_test_data(file_path: str) -> str:
    with pathlib.Path(file_path).open(encoding="utf-8") as f:
        return f.read()


class TestXMLTrace(unittest.TestCase):

    def test_no_loop(self) -> None:
        trail_input = read_test_data("tests/test_data/trace_no_loop.spin")
        with self.assertRaises(exceptions.NoLoopError):
            spin_trace.parse(trail_input)

    def test_valid_trace(self) -> None:
        trail_input = read_test_data("tests/test_data/trace_valid.spin")
        trace = spin_trace.parse(trail_input)
        result = util.format_expect(
            common.markings_to_str(trace.to_markings(), trace.loop_start),
        )
        expected = util.format_expect(
            """
                                   1 1 1 1 1 1 1
               0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6
timer         │2│3│4│5│1│2│3│1│2│3│4│5│6│7│8│9│*│
randomWalk_p  │ │ │ │ │ │ │ │●│●│●│●│●│●│●│●│●│●│
leavingHome_p │ │ │ │ │●│●│●│ │ │ │ │ │ │ │ │ │ │
resting_p     │●│●│●│●│ │ │ │ │ │ │ │ │ │ │ │ │ │
=Lasso=                                        ⊔
        """,
        )
        self.assertEqual(result, expected)
