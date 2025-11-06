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

NUXMV_LOG = "nuXmv.log"
COMMANDS_FILE = "commands.txt"
MODEL_FILE = "model.smv"
TRACE_FILE_GLOB = "*_trace.xml"
TRACE_FILE = "trace.xml"


def get_diameter(tmpdir: Path, model_file: Path) -> int:
    """Get the diameter of the symbolic BDD FSM in the model file."""
    commands = [
        "set on_failure_script_quits 1\ngo\ncompute_reachable\nquit",
    ]
    with (tmpdir / COMMANDS_FILE).open("w", encoding="utf-8") as f:
        f.writelines(commands)
    shutil.copy(model_file, Path(tmpdir / MODEL_FILE))
    with (tmpdir / "diameter.log").open("w", encoding="utf-8") as nuxmv_log:
        subprocess.run(
            [
                util.NUXMV_PATH,
                "-source",
                tmpdir / COMMANDS_FILE,
                tmpdir / MODEL_FILE,
            ],
            cwd=tmpdir,
            stdout=nuxmv_log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    s = (tmpdir / "diameter.log").read_text(encoding="utf-8")
    assert "The computation of reachable states has been completed." in s
    assert "The diameter of the FSM is " in s
    s.split("The diameter of the FSM is ")
    # The [:-2] removes the trailing dot and newline from, e.g.,
    # "The diameter of the FSM is 42.\n"
    return int(s.split("The diameter of the FSM is ")[1][:-2])


def write_commands_file(
    tmpdir: Path,
    bound: int,
    loopback: int,
) -> None:
    with (tmpdir / COMMANDS_FILE).open("w", encoding="utf-8") as f:
        f.writelines(
            [
                "set on_failure_script_quits 1\n",
                "set counter_examples 1\n",
                "go_bmc\n",
                f'check_ltlspec_bmc_onepb -k "{bound}" -l "{loopback}"\n',
                f'show_traces -p {TRACE_PLUGIN} -o "{loopback}_{TRACE_FILE}"\n',
                "quit\n",
            ],
        )


def generate_model_file(
    tmpdir: Path,
    model_file: Path,
    formula: mtl.Mtl,
) -> None:
    ltlspec = mtl2ltlspec.main(custom_args.ModelChecker.NUXMV, formula)
    shutil.copy(model_file, Path(tmpdir / MODEL_FILE))
    with (tmpdir / MODEL_FILE).open("a", encoding="utf-8") as f:
        f.write(f"LTLSPEC {ltlspec};")


def model_check(tmpdir: Path) -> None:
    try:
        with (tmpdir / NUXMV_LOG).open("w", encoding="utf-8") as nuxmv_log:
            subprocess.run(
                [
                    util.NUXMV_PATH,
                    "-source",
                    tmpdir / COMMANDS_FILE,
                    tmpdir / MODEL_FILE,
                ],
                cwd=tmpdir,
                stdout=nuxmv_log,
                stderr=subprocess.STDOUT,
                check=True,
            )
    except subprocess.CalledProcessError:
        with (tmpdir / NUXMV_LOG).open("r", encoding="utf-8") as nuxmv_log:
            print("nuXmv log output:")
            for line in nuxmv_log:
                if line.startswith("*** ") or line.isspace():
                    continue
                print(f"  {line}", end="")
        raise


def analyse_file(
    trace_file: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
    show_markings: bool,  # noqa: FBT001
) -> tuple[mtl.Interval, analyse_cex.AnalyseCex]:
    analysis = analyse_cex.AnalyseCex(
        formula,
        de_bruijn,
        trace_file,
        custom_args.ModelChecker.NUXMV,
    )
    if show_markings:
        print(f"\n{analysis.get_markings()}")
    result = analysis.get_weakened_interval()
    if result is None:
        raise exceptions.NoWeakeningError
    return result, analysis


def analyse(
    tmpdir: Path,
    model_file: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
    bound: int,
    show_markings: bool,  # noqa: FBT001
) -> tuple[int, int | None]:
    results: list[mtl.Interval] = []
    for loopback in range(bound):
        write_commands_file(tmpdir, bound, loopback)
        generate_model_file(tmpdir, model_file, formula)
        model_check(tmpdir)
    for trace_file in tmpdir.glob(TRACE_FILE_GLOB):
        result, analysis = analyse_file(
            trace_file,
            formula,
            de_bruijn,
            show_markings,
        )
        results.append(result)
    if not results:
        raise exceptions.PropertyValidError
    return analysis.choose_weakest_interval(results)
