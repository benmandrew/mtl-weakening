import argparse
import contextlib
import io
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from src import analyse_cex, custom_args, mtl2ltlspec, util
from src.logic import ctx, mtl, parser

logger = logging.getLogger(__name__)


class Namespace(argparse.Namespace):
    mtl: str
    de_bruijn: list[int]
    log_level: str


def list_of_ints(arg: str) -> list[int]:
    return list(map(int, arg.split(",")))


def parse_args(argv: list[str]) -> Namespace:
    arg_parser = argparse.ArgumentParser(
        description="Convert MTL formula to SMV-compatible LTL specifications.",
    )
    custom_args.add_mtl_argument(arg_parser)
    custom_args.add_de_bruijn_argument(arg_parser)
    custom_args.add_log_level_arguments(arg_parser, default_level=logging.INFO)
    return arg_parser.parse_args(argv, namespace=Namespace())


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


# nuXmv trace plugins, controlled with flag `-p`:
#   0   BASIC TRACE EXPLAINER - shows changes only
#   1   BASIC TRACE EXPLAINER - shows all variables
#   2   TRACE TABLE PLUGIN - symbols on column
#   3   TRACE TABLE PLUGIN - symbols on row
#   4   TRACE XML DUMP PLUGIN - an xml document
#   5   TRACE COMPACT PLUGIN - Shows the trace in a compact tabular fashion
#   6   TRACE XML EMBEDDED DUMP PLUGIN - an xml element
#   7   Empty Trace Plugin
TRACE_PLUGIN = 4


def write_commands_file(
    tmpdir: Path,
    bound: int,
    loopback: int,
) -> None:
    commands = [
        "set on_failure_script_quits 1\n"
        "go_bmc\n"
        f'check_ltlspec_bmc_onepb -k "{bound}" -l "{loopback}" -o "problem"\n'
        f'show_traces -o "trace.xml" -p "{TRACE_PLUGIN}"\n'
        "quit",
    ]
    with (tmpdir / "commands.txt").open("w", encoding="utf-8") as f:
        f.writelines(commands)


INPUT_SMV_FILE = Path("models/foraging-robots.smv")


def call_mtl2ltlspec(formula: mtl.Mtl) -> str:
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        mtl2ltlspec.main(["--mtl", mtl.to_string(formula)])
    return f.getvalue()


def generate_model_file(tmpdir: Path, formula: mtl.Mtl) -> None:
    ltlspec = call_mtl2ltlspec(formula)
    shutil.copy(INPUT_SMV_FILE, Path(tmpdir / "model.smv"))
    with (tmpdir / "model.smv").open("a", encoding="utf-8") as f:
        f.write(f"LTLSPEC {ltlspec};")


def call_analyse_cex(
    tmpdir: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
) -> str:
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        analyse_cex.main(
            [
                "--mtl",
                mtl.to_string(formula),
                "--de-bruijn",
                ",".join(map(str, de_bruijn)),
                str(tmpdir / "trace.xml"),
            ],
        )
    return f.getvalue()


class PropertyValidError(Exception):
    pass


class NoWeakeningError(Exception):
    pass


def check_mtl(
    tmpdir: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
    bound: int,
    loopback: int,
) -> str:
    write_commands_file(tmpdir, bound, loopback)
    generate_model_file(tmpdir, formula)
    with (tmpdir / "nuXmv.log").open("w", encoding="utf-8") as nuxmv_log:
        subprocess.run(
            [
                "/usr/bin/nuXmv",
                "-source",
                tmpdir / "commands.txt",
                tmpdir / "model.smv",
            ],
            cwd=tmpdir,
            stdout=nuxmv_log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    with (tmpdir / "nuXmv.log").open("r", encoding="utf-8") as nuxmv_log:
        no_cex_string = (
            f"no counterexample found with bound {bound} and loop at {loopback}"
        )
        if no_cex_string in nuxmv_log.read():
            assert not Path(tmpdir / "trace.xml").exists()
            # Property is valid
            raise PropertyValidError
    result = call_analyse_cex(tmpdir, formula, de_bruijn)
    if result.startswith(analyse_cex.NO_WEAKENING_EXISTS_STR):
        raise NoWeakeningError
    return result


BOUND_MIN = 20
LOOPBACK = 1


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    util.setup_logging(args.log_level)
    context, subformula = get_context_and_subformula(args)
    bound = (
        BOUND_MIN
        if subformula.interval[1] is None
        else subformula.interval[1] * 2
    )
    bound = max(BOUND_MIN, bound)
    while True:
        formula = ctx.substitute(context, subformula)
        logger.info("Checking MTL formula %s", formula)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = check_mtl(
                    Path(tmpdir),
                    formula,
                    args.de_bruijn,
                    bound,
                    LOOPBACK,
                )
        except PropertyValidError:
            print("Final weakened interval:", subformula.interval)  # noqa: T201
            break
        except NoWeakeningError:
            print(analyse_cex.NO_WEAKENING_EXISTS_STR)  # noqa: T201
            break
        interval = parse_interval(result)
        bound = max(BOUND_MIN, interval[1] * 2)
        logger.info("Weakened %s to %s", subformula.interval, interval)
        subformula = substitute_interval(subformula, interval)


if __name__ == "__main__":
    main(sys.argv[1:])
