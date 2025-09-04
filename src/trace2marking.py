from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src import marking, util, xml_trace

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


def read_trace_input(args: Namespace) -> list[str]:
    if args.trace_file:
        return Path(args.trace_file).read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


def get_cex_trace(lines: list[str]) -> marking.Trace:
    return xml_trace.parse("".join(lines))


def main() -> None:
    args = parse_args()
    util.setup_logging(args.log_level)
    lines = read_trace_input(args)
    cex_trace = get_cex_trace(lines)
    result = marking.markings_to_str(
        cex_trace.to_markings(),
        cex_trace.loop_start,
    )
    print(result, end="")  # noqa: T201


if __name__ == "__main__":
    main()
