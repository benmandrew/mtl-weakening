import pathlib
import unittest

from src import util
from src.marking import common
from src.trace_analysis import exceptions, nuxmv_xml_trace


def read_test_data(file_path: str) -> str:
    with pathlib.Path(file_path).open(encoding="utf-8") as f:
        return f.read()


class TestXMLTrace(unittest.TestCase):

    def test_no_loop(self) -> None:
        xml_input = read_test_data("tests/test_data/trace_no_loop.xml")
        with self.assertRaises(exceptions.NoLoopError):
            nuxmv_xml_trace.parse(xml_input)

    def test_invalid_loop(self) -> None:
        xml_input = read_test_data("tests/test_data/trace_invalid_loop.xml")
        with self.assertRaises(AssertionError):
            nuxmv_xml_trace.parse(xml_input)

    def test_valid_trace(self) -> None:
        xml_input = read_test_data("tests/test_data/trace_valid.xml")
        trace = nuxmv_xml_trace.parse(xml_input)
        result = util.format_expect(
            common.markings_to_str(trace.to_markings(), trace.loop_start),
        )
        expected = util.format_expect(
            """
                   0 1 2
        MAX_TIMER │*│*│*│
        timer     │0│1│0│
        =Lasso=      └─┘
        """,
        )
        self.assertEqual(result, expected)
