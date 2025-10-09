import shutil
import subprocess
from pathlib import Path

from src import util
from src.logic import mtl
from src.trace_analysis import common

INPUT_PML_FILE = Path("models/foraging-robots.pml")


def generate_model_file(tmpdir: Path, formula: mtl.Mtl) -> None:
    ltlspec = common.call_mtl2ltlspec_spin(formula)
    shutil.copy(INPUT_PML_FILE, Path(tmpdir / "model.pml"))
    with (tmpdir / "model.pml").open("a", encoding="utf-8") as f:
        f.write("ltl formula\n{\n")
        f.write(f"  {ltlspec}\n")
        f.write("}\n")


def spin_generate_c(tmpdir: Path) -> None:
    subprocess.run(
        [
            util.SPIN_PATH,
            "-a",
            tmpdir / "model.pml",
        ],
        cwd=tmpdir,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def compile_pan(tmpdir: Path) -> None:
    subprocess.run(
        [
            util.GCC_PATH,
            "-o",
            "pan",
            "pan.c",
        ],
        cwd=tmpdir,
        check=True,
    )


def run_pan(tmpdir: Path) -> None:
    subprocess.run(
        [
            tmpdir / "pan",
            "-T",
            "-e",
            "-c1",
            "-a",
        ],
        cwd=tmpdir,
        check=True,
    )


def expand_trail_file(
    tmpdir: Path,
    trail_file: Path,
    output_file: Path,
) -> None:
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
    with output_file.open(
        "w",
        encoding="utf-8",
    ) as out:
        for line in expanded_trail.stdout.splitlines():
            # out.write(line + "\n")
            if line.startswith("@@@"):
                out.write(line[len("@@@ ") :] + "\n")
            elif line == "<<<<<START OF CYCLE>>>>>":
                out.write("START OF CYCLE\n")


def pick_longest_trail_file(tmpdir: Path, trail_files: list[Path]) -> Path:
    output_files: list[Path] = []
    for i, trail_file in enumerate(trail_files):
        output_file = tmpdir / f"trail_output_{i+1}.txt"
        with trail_file.open("r", encoding="utf-8") as inp, output_file.open(
            "w",
            encoding="utf-8",
        ) as out:
            for line in inp.readlines():
                if line.startswith("@@@"):
                    out.write(line[len("@@@ ") :])
        output_files.append(output_file)
    assert output_files, "No trail files found"
    return max(output_files, key=lambda p: sum(1 for _ in p.open()))


def check_mtl(
    tmpdir: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
) -> str:
    generate_model_file(tmpdir, formula)
    spin_generate_c(tmpdir)
    compile_pan(tmpdir)
    run_pan(tmpdir)
    trail_files = list(tmpdir.glob("model.pml*.trail"))
    output_files: list[Path] = []
    for i, trail_file in enumerate(trail_files):
        output_file = tmpdir / f"expanded_trail_{i+1}.txt"
        output_files.append(output_file)
        expand_trail_file(tmpdir, trail_file, output_file)
    longest_file = max(output_files, key=lambda p: sum(1 for _ in p.open()))
    # return longest_file.read_text(encoding="utf-8")
    print("FILE:", longest_file.read_text(encoding="utf-8"))
    return common.call_analyse_cex_spin(formula, de_bruijn, longest_file)
