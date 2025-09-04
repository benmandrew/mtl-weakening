from __future__ import annotations

import argparse
import logging
import sys
import typing
from pathlib import Path

from src import marking, util, weaken
from src.logic import ctx, parser
from src.trace_parsers import xml_dump

if typing.TYPE_CHECKING:
    import lark

    from src.logic import mtl

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    trace_file: Path | None
    log_level: str


def parse_args() -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    arg_parser.add_argument(
        "--mtl",
        type=str,
        required=True,
        help="MTL specification",
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


def read_trace_input(args: Namespace) -> list[str]:
    if args.trace_file:
        return Path(args.trace_file).read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


def get_cex_trace(model_parser: lark.Lark, lines: list[str]) -> marking.Trace:
    try:
        cex_trace = util.parse_nuxmv_output(model_parser, lines)
    except util.NoLinesError:
        util.eprint("Property is valid")
        sys.exit(1)
    if not cex_trace.find_loop():
        util.eprint("No loop exists in the counterexample")
        sys.exit(1)
    return cex_trace


def get_cex_trace_xml(lines: list[str]) -> marking.Trace:
    xml_element = xml_dump.parse("".join(lines))
    return xml_dump.xml_to_trace(xml_element)


def main() -> None:
    args = parse_args()
    util.setup_logging(args.log_level)
    formula = parser.parse_mtl(args.mtl)
    lines = read_trace_input(args)
    cex_trace = get_cex_trace_xml(lines)
    context, subformula = ctx.split_formula(formula, [0, 1])
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
