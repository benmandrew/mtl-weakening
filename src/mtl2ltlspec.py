import argparse

from src.logic import ltl, mtl, parser


class Namespace(argparse.Namespace):
    mtl: str
    sed: bool = False


def parse_args() -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Convert MTL formula to SMV-compatible LTL specifications.",
    )
    arg_parser.add_argument("mtl", type=str, help="MTL specification")
    arg_parser.add_argument(
        "--sed",
        action="store_true",
        help="Escape ampersands in the output for sed compatibility.",
    )
    return arg_parser.parse_args(namespace=Namespace())


def sed_escape(s: str) -> str:
    return s.replace("&", r"\&")


def main() -> None:
    args = parse_args()
    formula = parser.parse_mtl(args.mtl)
    smv = ltl.to_nuxmv(mtl.mtl_to_ltl(formula))
    if args.sed:
        smv = sed_escape(smv)
    print(smv)  # noqa: T201


if __name__ == "__main__":
    main()
