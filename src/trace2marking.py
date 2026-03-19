"""Command-line interface and utilities for trace parsing and marking."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from src import custom_args, marking
from src.trace_analysis import nuxmv_xml_trace

if TYPE_CHECKING:
    from pathlib import Path


class Namespace(argparse.Namespace):
    """Typed CLI namespace for trace-input arguments."""

    trace_file: Path | None


def parse_args(argv: list[str]) -> Namespace:
    """Parse CLI arguments for trace-to-marking conversion."""
    arg_parser = argparse.ArgumentParser(
        description="Analyse NuXmv output.",
    )
    custom_args.add_trace_file_argument(arg_parser)
    return arg_parser.parse_args(argv, namespace=Namespace())


def read_trace_input(trace_file: Path | None) -> list[str]:
    """Read trace content from file input or stdin."""
    if trace_file:
        return trace_file.read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


def get_cex_trace(lines: list[str]) -> marking.Trace:
    """Parse NuXmv XML trace lines into an internal trace object."""
    return nuxmv_xml_trace.parse("".join(lines))


def main(trace_file: Path | None) -> str:
    """Render a trace as a formatted markings table."""
    lines = read_trace_input(trace_file)
    cex_trace = get_cex_trace(lines)
    return marking.markings_to_str(
        cex_trace.to_markings(),
        cex_trace.loop_start,
    )


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    print(main(args.trace_file), end="")
