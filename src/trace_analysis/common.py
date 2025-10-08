import contextlib
import io
from pathlib import Path

from src import analyse_cex, mtl2ltlspec
from src.logic import mtl


class PropertyValidError(Exception):
    pass


class NoWeakeningError(Exception):
    pass


def call_mtl2ltlspec(formula: mtl.Mtl) -> str:
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        mtl2ltlspec.main(["--mtl", mtl.to_string(formula)])
    return f.getvalue()


def call_analyse_cex(
    tmpdir: Path,
    formula: mtl.Mtl,
    de_bruijn: list[int],
    trace_file_type: str,
) -> str:
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        analyse_cex.main(
            [
                "--mtl",
                mtl.to_string(formula),
                "--de-bruijn",
                ",".join(map(str, de_bruijn)),
                "--trace-file-type",
                trace_file_type,
                str(tmpdir / "trace.xml"),
            ],
        )
    return f.getvalue()
