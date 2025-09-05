import argparse
import sys

from src import custom_args
from src.logic import ltl, mtl, parser


class Namespace(argparse.Namespace):
    mtl: str


def parse_args(argv: list[str]) -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Convert MTL formula to SMV-compatible LTL specifications.",
    )
    custom_args.add_mtl_argument(arg_parser)
    return arg_parser.parse_args(argv, namespace=Namespace())


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    formula = parser.parse_mtl(args.mtl)
    smv = ltl.to_nuxmv(mtl.mtl_to_ltl(formula))
    print(smv)  # noqa: T201


if __name__ == "__main__":
    main(sys.argv[1:])
