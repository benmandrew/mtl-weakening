import shutil
import subprocess
from pathlib import Path

from src import analyse_cex
from src.logic import mtl
from src.trace_analysis import common, exceptions

# INPUT_SMV_FILE = Path("models/foraging-robots.smv")
INPUT_SMV_FILE = Path("models/foraging-robots-limit-search.smv")

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


def get_diameter(tmpdir: Path) -> int:
    """Get the diameter of the symbolic BDD FSM in the model file."""
    commands = [
        "set on_failure_script_quits 1\ngo\ncompute_reachable\nquit",
    ]
    with (tmpdir / "commands.txt").open("w", encoding="utf-8") as f:
        f.writelines(commands)
    shutil.copy(INPUT_SMV_FILE, Path(tmpdir / "model.smv"))
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


def generate_model_file(tmpdir: Path, formula: mtl.Mtl) -> None:
    ltlspec = common.call_mtl2ltlspec_nuxmv(formula)
    shutil.copy(INPUT_SMV_FILE, Path(tmpdir / "model.smv"))
    with (tmpdir / "model.smv").open("a", encoding="utf-8") as f:
        f.write(f"LTLSPEC {ltlspec};")


def model_check(tmpdir: Path) -> None:
    with (tmpdir / "nuXmv.log").open("w", encoding="utf-8") as nuxmv_log:
        subprocess.run(
            [
                "/usr/bin/nuXmv",
                # "-v",
                # "100",
                "-source",
                tmpdir / "commands.txt",
                tmpdir / "model.smv",
            ],
            cwd=tmpdir,
            stdout=nuxmv_log,
            stderr=subprocess.STDOUT,
            check=True,
        )


def check_mtl(
    tmpdir: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
    bound: int,
) -> str:
    write_commands_file(tmpdir, bound)
    generate_model_file(tmpdir, formula)
    model_check(tmpdir)
    with (tmpdir / "nuXmv.log").open("r", encoding="utf-8") as nuxmv_log:
        nuxmv_log.seek(0)
        # no_cex_string = (
        #     f"no counterexample found with bound {bound} and loop at {loopback}"
        # )
        no_cex_string = f"no counterexample found with bound {bound}"
        if no_cex_string in nuxmv_log.read():
            assert not Path(tmpdir / "trace.xml").exists()
            raise exceptions.PropertyValidError
    result = common.call_analyse_cex_nuxmv(tmpdir, formula, de_bruijn)
    if result.startswith(analyse_cex.NO_WEAKENING_EXISTS_STR):
        raise exceptions.NoWeakeningError
    return result
