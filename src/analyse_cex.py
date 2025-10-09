from __future__ import annotations

import argparse
import logging
import pathlib
import sys
import typing

from src import custom_args, marking, util, weaken
from src.logic import ctx, parser
from src.trace_analysis import nuxmv_xml_trace, spin_trace

if typing.TYPE_CHECKING:
    from src.logic import mtl

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    de_bruijn: list[int]
    trace_file: pathlib.Path | None
    model_checker: custom_args.ModelChecker
    log_level: str


def parse_args(argv: list[str]) -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    custom_args.add_mtl_argument(arg_parser)
    custom_args.add_de_bruijn_argument(arg_parser)
    custom_args.add_trace_file_argument(arg_parser)
    custom_args.add_model_checker_argument(arg_parser)
    custom_args.add_log_level_arguments(arg_parser)
    return arg_parser.parse_args(argv, namespace=Namespace())


def read_trace_input(args: Namespace) -> list[str]:
    if args.trace_file:
        return (
            pathlib.Path(args.trace_file)
            .read_text(encoding="utf-8")
            .splitlines()
        )
    return sys.stdin.readlines()


def get_cex_trace(args: Namespace, lines: list[str]) -> marking.Trace:
    if args.model_checker == custom_args.ModelChecker.nuxmv:
        return nuxmv_xml_trace.parse("".join(lines))
    if args.model_checker == custom_args.ModelChecker.spin:
        return spin_trace.parse("".join(lines))
    msg = f"Unknown model checker: {args.model_checker}"
    raise ValueError(msg)


NO_WEAKENING_EXISTS_STR = "No suitable weakening of the interval exists"


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    util.setup_logging(args.log_level)
    formula = parser.parse_mtl(args.mtl)
    lines = read_trace_input(args)
    cex_trace = get_cex_trace(args, lines)
    context, subformula = ctx.split_formula(formula, args.de_bruijn)
    context, subformula = ctx.partial_nnf(
        context,
        typing.cast("mtl.Temporal", subformula),
    )
    w = weaken.Weaken(context, subformula, cex_trace)
    interval = w.weaken()
    # print(w.markings)
    if interval is None:
        print(NO_WEAKENING_EXISTS_STR)
    else:
        print(util.interval_to_str(interval))


if __name__ == "__main__":
    main(sys.argv[1:])
