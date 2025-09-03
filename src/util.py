import json
import logging.config
import subprocess as sp
import sys
import typing
from pathlib import Path

import lark

from src import marking


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


def get_model_parser() -> lark.Lark:
    parser_path = Path(__file__).parent / "trace_parsers/basic.lark"
    with parser_path.open(encoding="utf-8") as f:
        return lark.Lark(f.read(), parser="lalr")


Value = int | bool | str


def str_to_value(s: str) -> Value:
    if s == "TRUE":
        return True
    if s == "FALSE":
        return False
    if s.isdigit():
        return int(s)
    return s


class TreeTransformer(lark.Transformer[lark.Token, marking.Trace]):
    INT = int
    CNAME = str

    def true(self, _: lark.Token) -> bool:
        return True

    def false(self, _: lark.Token) -> bool:
        return False

    def NEWLINE(self, _: lark.Token) -> object:  # noqa: N802
        return lark.Discard

    def start(self, tok: list[dict[str, Value]]) -> marking.Trace:
        return marking.Trace(tok)

    def expr(self, tok: list[Value]) -> Value:
        return tok[0]

    def state(self, tok: list[typing.Any]) -> dict[str, Value]:
        expr: list[typing.Any] = list(
            filter(lambda x: not isinstance(x, int), tok),
        )
        d = {}
        for e in expr:
            k, v = e.children
            d[k] = v
        return d


class NoLinesError(Exception):
    pass


def parse_nuxmv_output(
    model_parser: lark.Lark,
    lines: list[str],
) -> marking.Trace:
    filtered_lines = [
        line
        for line in lines
        if not line.isspace()
        and not line.startswith("*** ")
        and not line.startswith("-- ")
        and not line.startswith("Trace ")
    ]
    if not filtered_lines:
        raise NoLinesError
    parsetree = model_parser.parse("".join(filtered_lines))
    try:
        result = TreeTransformer().transform(parsetree)
    except lark.exceptions.VisitError as exn:
        if isinstance(exn.__context__, BaseException):
            # Reraise the original exception
            raise exn.__context__ from exn
        raise
    return result
