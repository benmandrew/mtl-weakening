import unittest

from src import marking as m


class TestTrace(unittest.TestCase):

    def test_lasso_indexing(self):
        trace = m.Trace([{"a": 5}, {"a": 10}, {"a": 2}], 1)
        self.assertEqual(trace[0]["a"], 5)
        self.assertEqual(trace[1]["a"], 10)
        self.assertEqual(trace[2]["a"], 2)
        self.assertEqual(trace[3]["a"], 10)
        self.assertEqual(trace[4]["a"], 2)
        self.assertEqual(trace[400]["a"], 2)
        self.assertEqual(trace[401]["a"], 10)
        self.assertEqual(trace[402]["a"], 2)


if __name__ == "__main__":
    unittest.main()
