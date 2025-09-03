from __future__ import annotations

import argparse
import logging
import sys
import typing
from pathlib import Path

import lark

from src import marking, util

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    trace_file: Path | None
    log_level: str


def parse_args() -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    arg_parser.add_argument(
        "trace_file",
        type=Path,
        default=None,
        help="Path to the trace file to analyse. If not provided, stdin will be used.",
    )
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


class NoLinesError(Exception):
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
        return marking.Trace(tok)

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


def read_trace_input(args: Namespace) -> list[str]:
    if args.trace_file:
        return Path(args.trace_file).read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


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
        raise NoLinesError
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
    model_parser = get_model_parser()
    lines = read_trace_input(args)
    try:
        cex_trace = parse_nuxmv_output(model_parser, lines)
    except NoLinesError:
        print("Trace is empty", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    if not cex_trace.find_loop():
        print("No loop found")  # noqa: T201
    else:
        print(f"Loop found at idx {cex_trace.loop_start}")  # noqa: T201
    result, _ = marking.markings_to_str(cex_trace.to_markings())
    print(result, end="")  # noqa: T201


if __name__ == "__main__":
    main()
