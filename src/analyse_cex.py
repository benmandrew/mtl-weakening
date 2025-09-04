from __future__ import annotations

import argparse
import logging
import pathlib
import sys
import typing

from src import custom_args, marking, util, weaken, xml_trace
from src.logic import ctx, parser

if typing.TYPE_CHECKING:
    from src.logic import mtl

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    de_bruijn: list[int]
    trace_file: pathlib.Path | None
    log_level: str


def parse_args() -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    custom_args.add_mtl_argument(arg_parser)
    custom_args.add_de_bruijn_argument(arg_parser)
    custom_args.add_trace_file_argument(arg_parser)
    custom_args.add_log_level_arguments(arg_parser)
    return arg_parser.parse_args(namespace=Namespace())


def read_trace_input(args: Namespace) -> list[str]:
    if args.trace_file:
        return (
            pathlib.Path(args.trace_file)
            .read_text(encoding="utf-8")
            .splitlines()
        )
    return sys.stdin.readlines()


def get_cex_trace(lines: list[str]) -> marking.Trace:
    return xml_trace.parse("".join(lines))


def main() -> None:
    args = parse_args()
    util.setup_logging(args.log_level)
    formula = parser.parse_mtl(args.mtl)
    lines = read_trace_input(args)
    cex_trace = get_cex_trace(lines)
    context, subformula = ctx.split_formula(formula, args.de_bruijn)
    context, subformula = ctx.partial_nnf(
        context,
        typing.cast("mtl.Temporal", subformula),
    )
    w = weaken.Weaken(context, subformula, cex_trace)
    interval = w.weaken()
    print(  # noqa: T201
        str(interval).replace(" ", "").replace("(", "[").replace(")", "]"),
    )


if __name__ == "__main__":
    main()
