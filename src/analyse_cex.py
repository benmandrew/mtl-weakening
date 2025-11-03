from __future__ import annotations

import argparse
import logging
import sys
import typing

from src import custom_args, marking, util, weaken
from src.logic import ctx, parser
from src.trace_analysis import nuxmv_xml_trace, spin_trace

if typing.TYPE_CHECKING:
    from pathlib import Path

    from src.logic import mtl

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    de_bruijn: list[int]
    trace_file: Path | None
    model_checker: custom_args.ModelChecker
    show_markings: bool
    log_level: str


def parse_args(argv: list[str]) -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description=(
            "Determine the optimal weakening "
            "of an MTL formula to satisfy a given trace."
        ),
    )
    custom_args.add_mtl_argument(arg_parser)
    custom_args.add_de_bruijn_argument(arg_parser)
    custom_args.add_trace_file_argument(arg_parser)
    custom_args.add_model_checker_argument(arg_parser)
    custom_args.add_show_markings_argument(arg_parser)
    custom_args.add_log_level_arguments(arg_parser)
    return arg_parser.parse_args(argv, namespace=Namespace())


def read_trace_input(trace_file: Path | None) -> list[str]:
    if trace_file:
        return trace_file.read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


def get_cex_trace(
    model_checker: custom_args.ModelChecker,
    lines: list[str],
) -> marking.Trace:
    if model_checker == custom_args.ModelChecker.NUXMV:
        return nuxmv_xml_trace.parse("".join(lines))
    if model_checker == custom_args.ModelChecker.SPIN:
        return spin_trace.parse("\n".join(lines))
    msg = f"Unknown model checker: {model_checker}"
    raise ValueError(msg)


def main(
    formula: mtl.Mtl,
    de_bruijn: list[int],
    trace_file: Path | None,
    model_checker: custom_args.ModelChecker,
    show_markings: bool = False,  # noqa: FBT001 FBT002
) -> str:
    lines = read_trace_input(trace_file)
    cex_trace = get_cex_trace(model_checker, lines)
    context, subformula = ctx.split_formula(formula, de_bruijn)
    context, subformula = ctx.partial_nnf(
        context,
        typing.cast("mtl.Temporal", subformula),
    )
    w = weaken.Weaken(context, subformula, cex_trace)
    interval = w.weaken()
    if show_markings:
        print(w.markings)
    if interval is None:
        return util.NO_WEAKENING_EXISTS_STR
    return util.interval_to_str(interval)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    util.setup_logging(args.log_level)
    mtl_formula = parser.parse_mtl(args.mtl)
    print(
        main(
            mtl_formula,
            args.de_bruijn,
            args.trace_file,
            args.model_checker,
            args.show_markings,
        ),
    )
