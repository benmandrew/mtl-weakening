import unittest

from src.logic import ltl, mtl, parser


class TestMtlToLtl(unittest.TestCase):
    def test_eventually_upper_bound(self) -> None:
        formula = parser.parse_mtl("F[2,4] p")
        expected = parser.parse_nuxmv_ltl("X (X (p | X (p | X (p))))")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_eventually_infinite_upper_bound(self) -> None:
        formula = parser.parse_mtl("F[1,∞] p")
        expected = parser.parse_nuxmv_ltl("X (F p)")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_always_upper_bound(self) -> None:
        formula = parser.parse_mtl("G[1,3] p")
        expected = parser.parse_nuxmv_ltl("X (p & X (p & X (p)))")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_always_infinite_upper_bound(self) -> None:
        formula = parser.parse_mtl("G[3,∞] p")
        expected = parser.parse_nuxmv_ltl("X (X (X (G p)))")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_until_upper_bound(self) -> None:
        formula = parser.parse_mtl("p U[1,2] q")
        expected = parser.parse_nuxmv_ltl("X (q | (p & X (q)))")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_until_infinite_upper_bound(self) -> None:
        formula = parser.parse_mtl("p U[2,∞] q")
        expected = parser.parse_nuxmv_ltl("X (X (p U q))")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_release_upper_bound(self) -> None:
        formula = parser.parse_mtl("p R[1,2] q")
        expected = parser.parse_nuxmv_ltl(
            "X ((q & X (q)) | (p & q) | (q & X (p & q)))",
        )
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_release_infinite_upper_bound(self) -> None:
        formula = parser.parse_mtl("p R[2,∞] q")
        expected = parser.parse_nuxmv_ltl("X (X (p R q))")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))
        formula = parser.parse_mtl("p R q")
        expected = parser.parse_nuxmv_ltl("(p R q)")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))

    def test_boolean(self) -> None:
        formula = parser.parse_mtl("TRUE & FALSE")
        expected = parser.parse_nuxmv_ltl("TRUE & FALSE")
        result = mtl.mtl_to_ltl(formula)
        self.assertEqual(ltl.to_nuxmv(result), ltl.to_nuxmv(expected))


class TestMtlToString(unittest.TestCase):
    def test_deep_nested_negations_and_temporal(self) -> None:
        formula = parser.parse_mtl(
            "a R (!(((p & !(F[1, 2] (q))) -> G[0, 3] ((!(r) | X (TRUE))))))",
        )
        self.assertEqual(
            mtl.to_string(formula),
            "(a R !(((p & !(F[1, 2] (q))) -> G[0, 3] ((!(r) | X (TRUE))))))",
        )

    def test_complex_mixed_with_next_and_implies(self) -> None:
        formula = parser.parse_mtl(
            "((FALSE -> X (F[2, 4] (q))) & !((r | (s U[1, 3] t))))",
        )
        self.assertEqual(
            mtl.to_string(formula),
            "((FALSE -> X (F[2, 4] (q))) & !((r | (s U[1, 3] t))))",
        )


if __name__ == "__main__":
    unittest.main()
