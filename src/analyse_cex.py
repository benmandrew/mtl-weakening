from __future__ import annotations

import argparse
import sys
import typing
from enum import Enum

from src import custom_args, marking, util, weaken
from src.logic import ctx, mtl, parser
from src.trace_analysis import nuxmv_xml_trace, spin_trace

if typing.TYPE_CHECKING:
    from pathlib import Path


class Namespace(argparse.Namespace):
    mtl: str
    de_bruijn: list[int]
    trace_file: Path | None
    model_checker: custom_args.ModelChecker
    show_markings: bool


def parse_args(argv: list[str]) -> Namespace:
    """Parse CLI arguments for counterexample-based interval analysis."""
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
    return arg_parser.parse_args(argv, namespace=Namespace())


def read_trace_input(trace_file: Path | None) -> list[str]:
    """Load trace text from a file or standard input."""
    if trace_file:
        return trace_file.read_text(encoding="utf-8").splitlines()
    return sys.stdin.readlines()


def get_cex_trace(
    model_checker: custom_args.ModelChecker,
    lines: list[str],
) -> marking.Trace:
    """Parse raw trace lines using the selected model-checker format."""
    if model_checker == custom_args.ModelChecker.NUXMV:
        return nuxmv_xml_trace.parse("".join(lines))
    if model_checker == custom_args.ModelChecker.SPIN:
        return spin_trace.parse("\n".join(lines))
    msg = f"Unknown model checker: {model_checker}"
    raise ValueError(msg)


class WeakeningType(Enum):
    EXTENSION = "extension"
    CONTRACTION = "contraction"


class AnalyseCex:
    def __init__(
        self,
        formula: mtl.Mtl,
        de_bruijn: list[int],
        trace_file: Path | None,
        model_checker: custom_args.ModelChecker,
    ) -> None:
        """Build analysis state for weakening one temporal subformula."""
        lines = read_trace_input(trace_file)
        cex_trace = get_cex_trace(model_checker, lines)
        context, subformula = ctx.split_formula(formula, de_bruijn)
        context, subformula = ctx.partial_nnf(
            context,
            typing.cast("mtl.Temporal", subformula),
        )
        self.w = weaken.Weaken(context, subformula, cex_trace)

    def get_markings(self) -> marking.Marking:
        """Return the computed truth markings for the analyzed formula."""
        return self.w.markings

    def get_weakened_interval(self) -> mtl.Interval | None:
        """Compute the best interval weakening for the selected subformula."""
        return self.w.weaken()

    def does_formula_hold(self, formula: mtl.Mtl) -> bool:
        """Check whether a formula holds at the initial trace position."""
        bl = self.w.markings[formula]
        if len(bl) == 0:
            return False
        assert isinstance(bl[0], bool)
        return bl[0]

    def get_weakening_type(self) -> WeakeningType:
        """Classify weakening as extension or contraction for the subformula."""
        if isinstance(self.w.subformula, (mtl.Eventually, mtl.Until)):
            return WeakeningType.EXTENSION
        if isinstance(self.w.subformula, (mtl.Always, mtl.Release)):
            return WeakeningType.CONTRACTION
        msg = f"Subformula '{self.w.subformula}' must be temporal"
        raise TypeError(msg)

    def choose_weakest_interval(
        self,
        intervals: list[mtl.Interval],
    ) -> mtl.Interval:
        """Select the weakest interval from candidate weakenings."""
        weakening_type = self.get_weakening_type()
        if weakening_type == WeakeningType.EXTENSION:
            return max(
                intervals,
                key=lambda interval: interval[1] or float("-inf"),
            )
        if weakening_type == WeakeningType.CONTRACTION:
            return min(
                intervals,
                key=lambda interval: interval[1] or float("inf"),
            )
        msg = f"Unknown weakening type: {weakening_type}"
        raise TypeError(msg)


def main(args: Namespace) -> None:
    """Run CLI analysis and print either a weakened interval or failure text."""
    mtl_formula = parser.parse_mtl(args.mtl)
    analysis = AnalyseCex(
        mtl_formula,
        args.de_bruijn,
        args.trace_file,
        args.model_checker,
    )
    if args.show_markings:
        print(analysis.get_markings())
    interval = analysis.get_weakened_interval()
    if interval is None:
        print(util.NO_WEAKENING_EXISTS_STR)
    else:
        print(util.interval_to_str(interval))


if __name__ == "__main__":
    main(parse_args(sys.argv[1:]))
