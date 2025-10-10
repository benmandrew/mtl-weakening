import unittest

from src.marking import common


class TestTrace(unittest.TestCase):

    def test_lasso_indexing(self) -> None:
        trace = common.Trace([{"a": 5}, {"a": 10}, {"a": 2}], 1)
        self.assertEqual(trace[0]["a"], 5)
        self.assertEqual(trace[1]["a"], 10)
        self.assertEqual(trace[2]["a"], 2)
        self.assertEqual(trace[3]["a"], 10)
        self.assertEqual(trace[4]["a"], 2)
        self.assertEqual(trace[400]["a"], 2)
        self.assertEqual(trace[401]["a"], 10)
        self.assertEqual(trace[402]["a"], 2)

    def test_finite_indexing(self) -> None:
        trace = common.Trace([{"a": 5}, {"a": 10}, {"a": 2}], None)
        self.assertEqual(trace[0]["a"], 5)
        self.assertEqual(trace[1]["a"], 10)
        self.assertEqual(trace[2]["a"], 2)
        self.assertTrue(trace[400]["a"])
        self.assertTrue(trace[401]["a"])
        self.assertTrue(trace[402]["a"])


if __name__ == "__main__":
    unittest.main()
