import argparse
import sys

from src import custom_args
from src.logic import ltl, mtl, parser


class Namespace(argparse.Namespace):
    model_checker: custom_args.ModelChecker
    mtl: str


def parse_args(argv: list[str]) -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description=(
            "Convert MTL formula to SMV- or Promela-compatible "
            "LTL specifications."
        ),
    )
    custom_args.add_mtl_argument(arg_parser)
    custom_args.add_model_checker_argument(arg_parser)
    return arg_parser.parse_args(argv, namespace=Namespace())


def main(model_checker: custom_args.ModelChecker, mtl_formula: mtl.Mtl) -> str:
    ltl_formula = mtl.mtl_to_ltl(mtl_formula)
    if model_checker == custom_args.ModelChecker.spin:
        return ltl.to_spin(ltl_formula)
    if model_checker == custom_args.ModelChecker.nuxmv:
        return ltl.to_nuxmv(ltl_formula)
    msg = f"Unsupported model checker: {model_checker}"
    raise ValueError(msg)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    formula = parser.parse_mtl(args.mtl)
    print(main(args.model_checker, formula))
