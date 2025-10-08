from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src import custom_args, marking, util
from src.trace_analysis import nuxmv_xml_trace

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    trace_file: Path | None
    log_level: str


def parse_args(argv: list[str]) -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    custom_args.add_trace_file_argument(arg_parser)
    custom_args.add_log_level_arguments(arg_parser)
    return arg_parser.parse_args(argv, namespace=Namespace())


def read_trace_input(args: Namespace) -> list[str]:
    if args.trace_file:
        return Path(args.trace_file).read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


def get_cex_trace(lines: list[str]) -> marking.Trace:
    return nuxmv_xml_trace.parse("".join(lines))


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    util.setup_logging(args.log_level)
    lines = read_trace_input(args)
    cex_trace = get_cex_trace(lines)
    result = marking.markings_to_str(
        cex_trace.to_markings(),
        cex_trace.loop_start,
    )
    print(result, end="")


if __name__ == "__main__":
    main(sys.argv[1:])
