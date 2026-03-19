"""CLI argument parsing utilities for model checking and trace analysis."""

import argparse
import pathlib
from enum import Enum


def _list_of_ints(arg: str) -> list[int]:
    """Parse a comma-separated list of integers for CLI argument handling."""
    return list(map(int, arg.split(",")))


def add_model_argument(parser: argparse.ArgumentParser) -> None:
    """Register the model-file argument on a CLI parser."""
    parser.add_argument(
        "--model",
        type=pathlib.Path,
        help="Path to the model file.",
    )


def add_mtl_argument(parser: argparse.ArgumentParser) -> None:
    """Register the MTL specification argument on a CLI parser."""
    parser.add_argument("--mtl", type=str, help="MTL specification")


def add_de_bruijn_argument(parser: argparse.ArgumentParser) -> None:
    """Register the De Bruijn selector argument on a CLI parser."""
    parser.add_argument(
        "--de-bruijn",
        type=_list_of_ints,
        help="De Bruijn index of the subformula as a list of integers",
    )


def add_trace_file_argument(parser: argparse.ArgumentParser) -> None:
    """Register an optional trace-file input argument on a CLI parser."""
    parser.add_argument(
        "trace_file",
        type=pathlib.Path,
        default=None,
        help="Path to the trace file to analyse. If not provided, stdin will be used.",
    )


class ModelChecker(Enum):
    """Supported backend model checkers for analysis workflows."""

    NUXMV = "nuxmv"
    SPIN = "spin"

    def __str__(self) -> str:
        """Return the enum name for CLI-facing display."""
        return self.name

    @staticmethod
    def from_string(s: str) -> "ModelChecker":
        """Convert a string token into a known model-checker enum value."""
        try:
            return ModelChecker[s]
        except KeyError as err:
            raise ValueError from err


def add_model_checker_argument(
    parser: argparse.ArgumentParser,
) -> None:
    """Register the model-checker selection argument on a CLI parser."""
    parser.add_argument(
        "--model-checker",
        type=ModelChecker.from_string,
        choices=list(ModelChecker),
        default=ModelChecker.NUXMV,
        help="The model checker used (default: NUXMV)",
    )


def add_show_markings_argument(
    parser: argparse.ArgumentParser,
) -> None:
    """Register a flag that prints computed markings during analysis."""
    parser.add_argument(
        "--show-markings",
        action="store_true",
        help="Show the markings computed during analysis.",
    )
