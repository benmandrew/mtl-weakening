import contextlib
import io
from pathlib import Path

from src import analyse_cex, mtl2ltlspec
from src.logic import mtl


def call_mtl2ltlspec_nuxmv(formula: mtl.Mtl) -> str:
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        mtl2ltlspec.main(
            ["--mtl", mtl.to_string(formula), "--model-checker", "nuxmv"],
        )
    return f.getvalue()


def call_mtl2ltlspec_spin(formula: mtl.Mtl) -> str:
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        mtl2ltlspec.main(
            ["--mtl", mtl.to_string(formula), "--model-checker", "spin"],
        )
    return f.getvalue()


def call_analyse_cex_nuxmv(
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
                "--model-checker",
                "nuxmv",
                str(tmpdir / "trace.xml"),
            ],
        )
    return f.getvalue()


def call_analyse_cex_spin(
    formula: mtl.Mtl,
    de_bruijn: list[int],
    trail_file: Path,
) -> str:
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        analyse_cex.main(
            [
                "--mtl",
                mtl.to_string(formula),
                "--de-bruijn",
                ",".join(map(str, de_bruijn)),
                "--model-checker",
                "spin",
                str(trail_file),
            ],
        )
    return f.getvalue()
