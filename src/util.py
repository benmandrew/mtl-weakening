import json
import logging.config
import pathlib
import subprocess as sp


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
    config_file = pathlib.Path("logging.conf")
    with config_file.open(encoding="utf-8") as f:
        config = json.load(f)
    config["loggers"]["root"]["level"] = loglevel
    logging.config.dictConfig(config)
