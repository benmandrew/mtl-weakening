import argparse
import logging

import sh  # type: ignore[import-untyped]

from src import util
from src.logic import ctx, mtl, parser

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    de_bruijn: list[int]
    log_level: str


def list_of_ints(arg: str) -> list[int]:
    return list(map(int, arg.split(",")))


def parse_args() -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Convert MTL formula to SMV-compatible LTL specifications.",
    )
    arg_parser.add_argument("--mtl", type=str, help="MTL specification")
    arg_parser.add_argument(
        "--de-bruijn",
        type=list_of_ints,
        help="De Bruijn index of the subformula as a list of integers",
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


def get_context_and_subformula(args: Namespace) -> tuple[ctx.Ctx, mtl.Temporal]:
    formula = parser.parse_mtl(args.mtl)
    context, subformula = ctx.split_formula(formula, args.de_bruijn)
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
BOUND_MAX = 100
LOOPBACK = 1

CHECK_MTL_COMMAND = sh.Command("experiments/check_mtl.sh")


def main() -> None:
    args = parse_args()
    util.setup_logging(args.log_level)
    context, subformula = get_context_and_subformula(args)
    bound = (
        BOUND_MAX
        if subformula.interval[1] is None
        else subformula.interval[1] * 2
    )
    bound = max(BOUND_MIN, bound)
    while True:
        formula = mtl.to_string(ctx.substitute(context, subformula))
        logger.info("Checking MTL formula %s", formula)
        de_bruijn = ",".join(map(str, args.de_bruijn))
        result = CHECK_MTL_COMMAND(
            formula,
            de_bruijn,
            str(bound),
            str(LOOPBACK),
        )
        assert isinstance(result, str)
        result = result.strip()
        if result == "Property is valid":
            break
        interval = parse_interval(result)
        logger.info("Weakened %s to %s", subformula.interval, interval)
        subformula = substitute_interval(subformula, interval)
    print("Final weakened interval:", subformula.interval)  # noqa: T201


if __name__ == "__main__":
    main()
