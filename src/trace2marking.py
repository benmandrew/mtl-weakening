from __future__ import annotations

import argparse
import logging
import sys
from typing import TYPE_CHECKING

from src import custom_args, util
from src.marking import common
from src.trace_analysis import nuxmv_xml_trace

if TYPE_CHECKING:
    from pathlib import Path

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


def read_trace_input(trace_file: Path | None) -> list[str]:
    if trace_file:
        return trace_file.read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


def get_cex_trace(lines: list[str]) -> common.Trace:
    return nuxmv_xml_trace.parse("".join(lines))


def main(trace_file: Path | None) -> str:
    lines = read_trace_input(trace_file)
    cex_trace = get_cex_trace(lines)
    return common.markings_to_str(
        cex_trace.to_markings(),
        cex_trace.loop_start,
    )


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    util.setup_logging(args.log_level)
    print(main(args.trace_file), end="")
