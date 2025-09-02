from __future__ import annotations

import argparse
import logging
import sys
import typing
from pathlib import Path

import lark

from src import marking, util, weaken
from src.logic import ctx, parser

if typing.TYPE_CHECKING:
    from src.logic import mtl

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    log_level: str


def parse_args() -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    arg_parser.add_argument("mtl", type=str, help="MTL specification")
    group = arg_parser.add_mutually_exclusive_group()
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
    arg_parser.set_defaults(log_level=logging.WARNING)
    return arg_parser.parse_args(namespace=Namespace())


Value = int | bool | str


class NoCounterexampleError(Exception):
    pass


class NoLoopError(Exception):
    pass


class TreeTransformer(lark.Transformer[lark.Token, marking.Trace]):
    INT = int
    CNAME = str

    def true(self, _: lark.Token) -> bool:
        return True

    def false(self, _: lark.Token) -> bool:
        return False

    def NEWLINE(self, _: lark.Token) -> object:  # noqa: N802
        return lark.Discard

    def start(self, tok: list[dict[str, Value]]) -> marking.Trace:
        trace = marking.Trace(tok)
        if not trace.find_loop():
            raise NoLoopError
        return trace

    def expr(self, tok: list[Value]) -> Value:
        return tok[0]

    def state(self, tok: list[typing.Any]) -> dict[str, Value]:
        expr: list[typing.Any] = list(
            filter(lambda x: not isinstance(x, int), tok),
        )
        d = {}
        for e in expr:
            k, v = e.children
            d[k] = v
        return d


def get_model_parser() -> lark.Lark:
    parser_path = Path(__file__).parent / "check_model.lark"
    with parser_path.open(encoding="utf-8") as f:
        return lark.Lark(f.read(), parser="lalr")


def parse_nuxmv_output(
    model_parser: lark.Lark,
    lines: list[str],
) -> marking.Trace:
    filtered_lines = [
        line
        for line in lines
        if not line.isspace()
        and not line.startswith("*** ")
        and not line.startswith("-- ")
        and not line.startswith("Trace ")
    ]
    if not filtered_lines:
        raise NoCounterexampleError
    parsetree = model_parser.parse("".join(filtered_lines))
    try:
        result = TreeTransformer().transform(parsetree)
    except lark.exceptions.VisitError as exn:
        if isinstance(exn.__context__, BaseException):
            # Reraise the original exception
            raise exn.__context__ from exn
        raise
    return result


def main() -> None:
    args = parse_args()
    util.setup_logging(args.log_level)
    formula = parser.parse_mtl(args.mtl)
    model_parser = get_model_parser()
    lines = sys.stdin.readlines()
    try:
        cex_trace = parse_nuxmv_output(model_parser, lines)
    except NoLoopError:
        print("No loop exists in the counterexample")  # noqa: T201
        sys.exit(1)
    except NoCounterexampleError:
        print("Property is valid")  # noqa: T201
        sys.exit(1)
    context, subformula = ctx.split_formula(formula, [0, 1])
    context, subformula = ctx.partial_nnf(
        context,
        typing.cast("mtl.Temporal", subformula),
    )
    w = weaken.Weaken(context, subformula, cex_trace)
    # print(w.markings)
    interval = w.weaken()
    print(str(interval).replace(" ", ""))  # noqa: T201


if __name__ == "__main__":
    main()
