import shutil
import subprocess
from pathlib import Path

from src import util

INPUT_PML_FILE = Path("experiments/foraging-robots.pml")


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
            "-c20",
            "-a",
        ],
        cwd=tmpdir,
        check=True,
    )


def pick_longest_trail_file(tmpdir: Path, trail_files: list[Path]) -> Path:
    output_files: list[Path] = []
    for i, trail_file in enumerate(trail_files):
        output_file = tmpdir / f"trail_output_{i}.txt"
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


def check_mtl_spin(
    tmpdir: Path,
    # formula: mtl.Mtl,
    # de_bruijn: list[int],
) -> str:
    shutil.copy(INPUT_PML_FILE, Path(tmpdir / "model.pml"))
    spin_generate_c(tmpdir)
    compile_pan(tmpdir)
    run_pan(tmpdir)
    trail_files = list(tmpdir.glob("foraging-robots.pml*.trail"))
    longest_file = pick_longest_trail_file(tmpdir, trail_files)
    return longest_file.read_text(encoding="utf-8")
