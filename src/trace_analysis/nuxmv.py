import shutil
import subprocess
from pathlib import Path

from src import analyse_cex, custom_args, mtl2ltlspec, util
from src.logic import mtl
from src.trace_analysis import exceptions

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


def get_diameter(tmpdir: Path, model_file: Path) -> int:
    """Get the diameter of the symbolic BDD FSM in the model file."""
    commands = [
        "set on_failure_script_quits 1\ngo\ncompute_reachable\nquit",
    ]
    with (tmpdir / "commands.txt").open("w", encoding="utf-8") as f:
        f.writelines(commands)
    shutil.copy(model_file, Path(tmpdir / "model.smv"))
    with (tmpdir / "nuXmv.log").open("w", encoding="utf-8") as nuxmv_log:
        subprocess.run(
            [
                util.NUXMV_PATH,
                "-source",
                tmpdir / "commands.txt",
                tmpdir / "model.smv",
            ],
            cwd=tmpdir,
            stdout=nuxmv_log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    s = (tmpdir / "nuXmv.log").read_text(encoding="utf-8")
    assert "The computation of reachable states has been completed." in s
    assert "The diameter of the FSM is " in s
    s.split("The diameter of the FSM is ")
    # The [:-2] removes the trailing dot and newline from, e.g.,
    # "The diameter of the FSM is 42.\n"
    return int(s.split("The diameter of the FSM is ")[1][:-2])


def write_commands_file(
    tmpdir: Path,
    bound: int,
) -> None:
    commands = [
        "set on_failure_script_quits 1\n"
        "go_bmc\n"
        f'check_ltlspec_bmc_onepb -k "{bound}" -l "*" -o "problem"\n'
        f'show_traces -o "trace.xml" -p "{TRACE_PLUGIN}"\n'
        "quit",
    ]
    with (tmpdir / "commands.txt").open("w", encoding="utf-8") as f:
        f.writelines(commands)


def generate_model_file(
    tmpdir: Path,
    model_file: Path,
    formula: mtl.Mtl,
) -> None:
    ltlspec = mtl2ltlspec.main(custom_args.ModelChecker.NUXMV, formula)
    shutil.copy(model_file, Path(tmpdir / "model.smv"))
    with (tmpdir / "model.smv").open("a", encoding="utf-8") as f:
        f.write(f"LTLSPEC {ltlspec};")


def model_check(tmpdir: Path) -> None:
    with (tmpdir / "nuXmv.log").open("w", encoding="utf-8") as nuxmv_log:
        subprocess.run(
            [
                util.NUXMV_PATH,
                "-source",
                tmpdir / "commands.txt",
                tmpdir / "model.smv",
            ],
            cwd=tmpdir,
            stdout=nuxmv_log,
            stderr=subprocess.STDOUT,
            check=True,
        )


def analyse(  # noqa: PLR0913 pylint: disable=too-many-arguments too-many-positional-arguments
    tmpdir: Path,
    model_file: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
    bound: int,
    show_markings: bool,  # noqa: FBT001
) -> tuple[int, int | None]:
    write_commands_file(tmpdir, bound)
    generate_model_file(tmpdir, model_file, formula)
    model_check(tmpdir)
    with (tmpdir / "nuXmv.log").open("r", encoding="utf-8") as nuxmv_log:
        no_cex_string = f"no counterexample found with bound {bound}"
        if no_cex_string in nuxmv_log.read():
            assert not Path(tmpdir / "trace.xml").exists()
            raise exceptions.PropertyValidError
    analysis = analyse_cex.AnalyseCex(
        formula,
        de_bruijn,
        tmpdir / "trace.xml",
        custom_args.ModelChecker.NUXMV,
    )
    if show_markings:
        print(f"\n{analysis.get_markings()}")
    result = analysis.get_weakened_interval()
    if result is None:
        raise exceptions.NoWeakeningError
    return result
