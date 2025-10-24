import shutil
import subprocess
from pathlib import Path

from src import analyse_cex, custom_args, mtl2ltlspec, util
from src.logic import mtl
from src.trace_analysis import exceptions


def generate_model_file(
    tmpdir: Path,
    model_file: Path,
    formula: mtl.Mtl,
) -> None:
    ltlspec = mtl2ltlspec.main(custom_args.ModelChecker.SPIN, formula)
    shutil.copy(model_file, Path(tmpdir / "model.pml"))
    with (tmpdir / "model.pml").open("a", encoding="utf-8") as f:
        f.write("ltl formula\n{\n")
        f.write(f"  {ltlspec}\n")
        f.write("}\n")


def spin_generate_c(tmpdir: Path) -> None:
    try:
        with (tmpdir / "spin.log").open("w", encoding="utf-8") as log_file:
            subprocess.run(
                [
                    util.SPIN_PATH,
                    "-a",
                    tmpdir / "model.pml",
                ],
                cwd=tmpdir,
                check=True,
                stdout=log_file,
            )
    except subprocess.CalledProcessError:
        print("Error during Spin compilation:")
        with (tmpdir / "spin.log").open("r", encoding="utf-8") as log_file:
            print(log_file.read())
        raise


def compile_pan(tmpdir: Path) -> None:
    subprocess.run(
        [
            util.GCC_PATH,
            "-DNP",
            "-o",
            "pan",
            "pan.c",
        ],
        cwd=tmpdir,
        check=True,
    )


N_COUNTEREXAMPLES = 1


def run_pan(tmpdir: Path) -> None:
    subprocess.run(
        [tmpdir / "pan", "-T", "-e", f"-c{N_COUNTEREXAMPLES}", "-l"],
        cwd=tmpdir,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def expand_trail_file(
    tmpdir: Path,
    trail_file: Path,
    output_file: Path,
) -> bool:
    expanded_trail = subprocess.run(
        [
            util.SPIN_PATH,
            "-T",
            "-p",
            "-k",
            trail_file,
            "-l",
            "-g",
            tmpdir / "model.pml",
        ],
        cwd=tmpdir,
        check=True,
        capture_output=True,
        text=True,
    )
    has_loop = False
    with output_file.open(
        "w",
        encoding="utf-8",
    ) as out:
        for line in expanded_trail.stdout.splitlines():
            if line.startswith("@@@"):
                out.write(line[len("@@@ ") :] + "\n")
            elif line == "<<<<<START OF CYCLE>>>>>":
                has_loop = True
                out.write("START OF CYCLE\n")
    # print(expanded_trail.stdout)
    return has_loop


def check_mtl(
    tmpdir: Path,
    model_file: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
) -> tuple[int, int]:
    generate_model_file(tmpdir, model_file, formula)
    spin_generate_c(tmpdir)
    compile_pan(tmpdir)
    run_pan(tmpdir)
    trail_files = list(tmpdir.glob("model.pml*.trail"))
    if not trail_files:
        raise exceptions.PropertyValidError
    output_files: list[Path] = []
    for i, trail_file in enumerate(trail_files):
        output_file = tmpdir / f"expanded_trail_{i+1}.txt"
        expand_trail_file(tmpdir, trail_file, output_file)
        output_files.append(output_file)
    results: list[tuple[int, int]] = []
    for file in output_files:
        result = analyse_cex.main(
            formula,
            de_bruijn,
            file,
            custom_args.ModelChecker.SPIN,
        )
        if result.startswith(util.NO_WEAKENING_EXISTS_STR):
            raise exceptions.NoWeakeningError
        results.append(util.str_to_interval(result))
    return max(results, key=lambda interval: interval[1])
