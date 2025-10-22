import argparse
import logging
import sys
import tempfile
from pathlib import Path

from src import custom_args, util
from src.logic import ctx, mtl, parser
from src.trace_analysis import exceptions, nuxmv, spin

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    model_checker: custom_args.ModelChecker
    model: Path
    mtl: str
    de_bruijn: list[int]
    log_level: str


def parse_args(argv: list[str]) -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Convert MTL formula to SMV-compatible LTL specifications.",
    )
    custom_args.add_model_checker_argument(arg_parser)
    custom_args.add_model_argument(arg_parser)
    custom_args.add_mtl_argument(arg_parser)
    custom_args.add_de_bruijn_argument(arg_parser)
    custom_args.add_log_level_arguments(arg_parser)
    return arg_parser.parse_args(argv, namespace=Namespace())


def get_context_and_subformula(
    mtl_str: str,
    de_bruijn: list[int],
) -> tuple[ctx.Ctx, mtl.Temporal]:
    formula = parser.parse_mtl(mtl_str)
    context, subformula = ctx.split_formula(formula, de_bruijn)
    assert isinstance(subformula, mtl.Temporal)
    return ctx.partial_nnf(
        context,
        subformula,
    )


def parse_interval(interval: str) -> tuple[int, int]:
    interval = interval.replace(" ", "").replace("[", "").replace("]", "")
    start, end = map(int, interval.split(","))
    return start, end


def substitute_interval(
    formula: mtl.Temporal,
    interval: tuple[int, int],
) -> mtl.Temporal:
    if isinstance(formula, mtl.Always):
        return mtl.Always(formula.operand, interval)
    if isinstance(formula, mtl.Eventually):
        return mtl.Eventually(formula.operand, interval)
    if isinstance(formula, mtl.Until):
        return mtl.Until(formula.left, formula.right, interval)
    if isinstance(formula, mtl.Release):
        return mtl.Release(formula.left, formula.right, interval)
    msg = f"Formula '{formula}' must be temporal"
    raise ValueError(msg)


BOUND_MIN = 20


def main_nuxmv(model_file: Path, mtl_str: str, de_bruijn: list[int]) -> None:
    context, subformula = get_context_and_subformula(mtl_str, de_bruijn)
    de_bruijn = ctx.get_de_bruijn(context)
    bound = (
        BOUND_MIN
        if subformula.interval[1] is None
        else int(subformula.interval[1] * 1.5)
    )
    bound = max(BOUND_MIN, bound)
    n_iterations = 0
    while True:
        formula = ctx.substitute(context, subformula)
        print(
            f"Bound {bound}: {util.interval_to_str(subformula.interval)} → ",
            end="",
        )
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = nuxmv.check_mtl(
                    Path(tmpdir),
                    model_file,
                    formula,
                    de_bruijn,
                    bound,
                )
        except exceptions.PropertyValidError:
            print(
                f"Final weakened interval in {n_iterations} "
                f"iterations: {subformula.interval}",
            )
            break
        except exceptions.NoWeakeningError:
            print(util.NO_WEAKENING_EXISTS_STR)
            break
        except exceptions.NoLoopError:
            print(
                "No loop found in the trace, decreasing bound and retrying",
            )
            bound -= 1
            continue
        interval = parse_interval(result)
        bound = max(BOUND_MIN, int(interval[1] * 1.5))
        print(util.interval_to_str(interval))
        subformula = substitute_interval(subformula, interval)
        n_iterations += 1


def main_spin(model_file: Path, mtl_str: str, de_bruijn: list[int]) -> None:
    context, subformula = get_context_and_subformula(mtl_str, de_bruijn)
    de_bruijn = ctx.get_de_bruijn(context)
    n_iterations = 0
    while True:
        formula = ctx.substitute(context, subformula)
        print(
            f"{util.interval_to_str(subformula.interval)} → ",
            end="\n",
        )
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = spin.check_mtl(
                    Path(tmpdir),
                    model_file,
                    formula,
                    de_bruijn,
                )
        except exceptions.PropertyValidError:
            print(
                f"Final weakened interval in {n_iterations} "
                f"iterations: {subformula.interval}",
            )
            break
        except exceptions.NoWeakeningError:
            print(util.NO_WEAKENING_EXISTS_STR)
            break
        interval = parse_interval(result)
        # print(util.interval_to_str(interval))
        subformula = substitute_interval(subformula, interval)
        n_iterations += 1


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    util.setup_logging(args.log_level)
    if args.model_checker == custom_args.ModelChecker.nuxmv:
        main_nuxmv(args.model, args.mtl, args.de_bruijn)
    else:
        main_spin(args.model, args.mtl, args.de_bruijn)
