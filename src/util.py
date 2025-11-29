from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.logic import mtl

SPIN_PATH = Path(os.getenv("SPIN_PATH", "/usr/local/bin/spin"))
NUXMV_PATH = Path(os.getenv("NUXMV_PATH", "/usr/bin/nuXmv"))
GCC_PATH = Path(os.getenv("GCC_PATH", "/usr/bin/gcc"))


NO_WEAKENING_EXISTS_STR = "No suitable weakening of the interval exists"


def eprint(  # type: ignore[no-untyped-def]
    *args,  # noqa: ANN002
    **kwargs,  # noqa: ANN003
) -> None:
    print(*args, file=sys.stderr, **kwargs)


Value = int | bool | str


def str_to_value(s: str) -> Value:
    if s == "TRUE":
        return True
    if s == "FALSE":
        return False
    if s.isdigit():
        return int(s)
    return s


def format_expect(s: str) -> str:
    return textwrap.dedent(s).strip("\n")


def interval_to_str(interval: mtl.Interval) -> str:
    start, end = interval
    end_str = str(end) if end is not None else "∞"
    return f"[{start},{end_str}]"


def str_to_interval(interval: str) -> mtl.Interval:
    interval = interval.replace(" ", "").replace("[", "").replace("]", "")
    start_str, end_str = interval.split(",")
    start = int(start_str)
    end = int(end_str) if end_str != "∞" else None
    return start, end
