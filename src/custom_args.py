import argparse
import logging
import pathlib
from enum import Enum


def _list_of_ints(arg: str) -> list[int]:
    return list(map(int, arg.split(",")))


def add_mtl_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mtl", type=str, help="MTL specification")


def add_de_bruijn_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--de-bruijn",
        type=_list_of_ints,
        help="De Bruijn index of the subformula as a list of integers",
    )


def add_trace_file_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "trace_file",
        type=pathlib.Path,
        default=None,
        help="Path to the trace file to analyse. If not provided, stdin will be used.",
    )


class TraceFileType(Enum):
    nuxmv_xml = "nuxmv_xml"
    spin = "spin"

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def from_string(s: str) -> "TraceFileType":
        try:
            return TraceFileType[s]
        except KeyError as err:
            raise ValueError from err


def add_trace_file_type_argument(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--trace-file-type",
        type=TraceFileType.from_string,
        choices=list(TraceFileType),
        default=TraceFileType.nuxmv_xml,
        help="Type of the trace file (default: nuxmv_xml)",
    )


def add_log_level_arguments(
    parser: argparse.ArgumentParser,
    default_level: int = logging.WARNING,
) -> None:
    group = parser.add_mutually_exclusive_group()
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
    parser.set_defaults(log_level=default_level)
