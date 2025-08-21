from __future__ import annotations

import argparse
import pathlib
import sys

import lark

from src import marking
from src.logic import parser


class Namespace(argparse.Namespace):
    mtl: str


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    parser.add_argument("mtl", type=str, help="MTL specification")
    return parser.parse_args(namespace=Namespace())


class TreeTransformer(lark.Transformer):
    INT = int
    CNAME = str
    true = lambda _self, _: True  # noqa: E731
    false = lambda _self, _: False  # noqa: E731
    NEWLINE = lambda _self, _: lark.Discard  # noqa: E731

    def start(self, tok: list) -> marking.Trace:
        return marking.Trace(tok)

    def expr(self, tok: list[int | bool | str]) -> int | bool | str:
        return tok[0]

    def state(self, tok: list) -> dict:
        expr: list[lark.tree.Tree] = list(
            filter(lambda x: type(x) is not int, tok),
        )
        d = {}
        for e in expr:
            k, v = e.children
            d[k] = v
        return d


def get_model_parser() -> lark.Lark:
    parser_path = pathlib.Path("res/check_model.lark")
    with parser_path.open(encoding="utf-8") as f:
        return lark.Lark(f.read(), parser="lalr")


def main() -> None:
    args = parse_args()
    model_parser = get_model_parser()
    formula = parser.parse_mtl(args.mtl)
    nuxmv_output = sys.stdin.readlines()
    nuxmv_output = [
        line
        for line in nuxmv_output
        if not line.isspace()
        and not line.startswith("*** ")
        and not line.startswith("-- ")
        and not line.startswith("Trace ")
    ]
    parsetree = model_parser.parse("".join(nuxmv_output))
    cex: marking.Trace = TreeTransformer().transform(parsetree)
    markings = marking.Marking(cex, formula)
    print(markings)  # noqa: T201


if __name__ == "__main__":
    main()
