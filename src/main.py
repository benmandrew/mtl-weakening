from __future__ import annotations

import pathlib

from lark import Discard, Lark, Transformer

from src import marking
from src.logic import ltl, mtl


class TreeTransformer(Transformer):
    INT = int
    WORD = str
    true = lambda _self, _: True  # noqa: E731
    false = lambda _self, _: False  # noqa: E731
    NL = lambda _self, _: Discard  # noqa: E731

    def start(self, tok: list) -> marking.Trace:
        return marking.Trace(tok)

    def expr(self, tok: list) -> int | bool:
        return tok[0]

    def state(self, tok: list) -> dict:
        expr = list(filter(lambda x: type(x) is not int, tok))
        d = {}
        for e in expr:
            k, v = e.children
            d[k] = v
        return d


def sed_escape(s: str) -> str:
    return s.replace("&", r"\&")


def main() -> None:

    parser_path = pathlib.Path("res/check_model.lark")
    with parser_path.open(encoding="utf-8") as f:
        _parser = Lark(f.read(), parser="lalr")

    mtl_fmla = mtl.Always(mtl.Eventually(mtl.Prop("trigger"), (0, 4)))
    _mtl_string = mtl.to_string(mtl_fmla)
    _ltlspec = ltl.to_nuxmv(mtl.mtl_to_ltl(mtl_fmla))

    formula = mtl.Not(mtl.Always(mtl.Eventually(mtl.Prop("p"), (0, 2))))
    trace = marking.Trace(
        [
            {"p": False},
            {"p": False},
            {"p": True},
        ],
        0,
    )
    markings = marking.Marking(trace, formula)
    formula = mtl.Not(mtl.Always(mtl.Eventually(mtl.Prop("p"), (0, 1))))
    markings[formula]
    # w = weaken.Weaken(formula, indices, trace).weaken()


if __name__ == "__main__":
    main()
