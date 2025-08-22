from __future__ import annotations

import argparse
import logging
import pathlib
import sys
import typing

import lark

from src import marking, util, weaken
from src.logic import ctx, mtl, parser

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    log_level: str


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    parser.add_argument("mtl", type=str, help="MTL specification")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--quiet",
        action="store_const",
        dest="log_level",
        const=logging.ERROR,
    )
    group.add_argument(
        "--debug",
        action="store_const",
        dest="log_level",
        const=logging.DEBUG,
    )
    parser.set_defaults(log_level=logging.INFO)
    return parser.parse_args(namespace=Namespace())


class TreeTransformer(lark.Transformer):
    INT = int
    CNAME = str
    true = lambda _self, _: True  # noqa: E731
    false = lambda _self, _: False  # noqa: E731
    NEWLINE = lambda _self, _: lark.Discard  # noqa: E731

    def start(self, tok: list) -> marking.Trace:
        trace = marking.Trace(tok)
        trace.find_loop()
        return trace

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


def parse_nuxmv_output(
    model_parser: lark.Lark,
    lines: list[str],
) -> marking.Trace | None:
    filtered_lines = [
        line
        for line in lines
        if not line.isspace()
        and not line.startswith("*** ")
        and not line.startswith("-- ")
        and not line.startswith("Trace ")
    ]
    if not filtered_lines:
        return None
    parsetree = model_parser.parse("".join(filtered_lines))
    return TreeTransformer().transform(parsetree)


def main() -> None:
    args = parse_args()
    util.setup_logging(args.log_level)
    formula = parser.parse_mtl(args.mtl)
    model_parser = get_model_parser()
    lines = sys.stdin.readlines()
    cex_trace = parse_nuxmv_output(model_parser, lines)
    if cex_trace is None:
        logger.error("No counterexample trace found.")
        sys.exit(1)
    context, subformula = ctx.split_formula(formula, [0, 1])
    context, subformula = ctx.partial_nnf(
        context,
        typing.cast("mtl.Temporal", subformula),
    )
    w = weaken.Weaken(context, subformula, cex_trace)
    print(w.markings)  # noqa: T201
    print(w.weaken())  # noqa: T201


if __name__ == "__main__":
    main()
