import json
import logging.config
import subprocess as sp
import sys
from pathlib import Path


def eprint(  # type: ignore[no-untyped-def]
    *args,  # noqa: ANN002
    **kwargs,  # noqa: ANN003
) -> None:
    print(*args, file=sys.stderr, **kwargs)  # noqa: T201


def run_and_capture(cmd: list[str]) -> str:
    out = []
    with sp.Popen(
        cmd,
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
        text=True,
        bufsize=1,
    ) as process:
        if process.stdout is None:
            msg = "Process stdout is None"
            raise RuntimeError(msg)
        for line in process.stdout:
            # Filter out nuXmv copyright output
            if line.startswith("*** ") or line.strip() == "":
                continue
            out.append(line)
        process.wait()
    return "".join(out)


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
