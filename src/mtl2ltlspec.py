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


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    mtl_formula = parser.parse_mtl(args.mtl)
    ltl_formula = mtl.mtl_to_ltl(mtl_formula)
    if args.model_checker == custom_args.ModelChecker.spin:
        print(ltl.to_spin(ltl_formula))
    elif args.model_checker == custom_args.ModelChecker.nuxmv:
        print(ltl.to_nuxmv(ltl_formula))
    else:
        msg = f"Unsupported model checker: {args.model_checker}"
        raise ValueError(msg)


if __name__ == "__main__":
    main(sys.argv[1:])
