from __future__ import annotations

import json
import logging.config
import sys
import textwrap
from pathlib import Path

SPIN_PATH = Path("/usr/local/bin/spin")
NUXMV_PATH = Path("/usr/bin/nuXmv")
GCC_PATH = Path("/usr/bin/gcc")


NO_WEAKENING_EXISTS_STR = "No suitable weakening of the interval exists"


def eprint(  # type: ignore[no-untyped-def]
    *args,  # noqa: ANN002
    **kwargs,  # noqa: ANN003
) -> None:
    print(*args, file=sys.stderr, **kwargs)


def setup_logging(loglevel: str) -> None:
    config_file = Path(__file__).parent / ".." / "logging.conf"
    with config_file.open(encoding="utf-8") as f:
        config = json.load(f)
    config["loggers"]["root"]["level"] = loglevel
    logging.config.dictConfig(config)


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


def interval_to_str(interval: tuple[int, int | None]) -> str:
    start, end = interval
    end_str = str(end) if end is not None else "∞"
    return f"[{start},{end_str}]"


def str_to_interval(interval: str) -> tuple[int, int]:
    interval = interval.replace(" ", "").replace("[", "").replace("]", "")
    start, end = map(int, interval.split(","))
    return start, end
