import subprocess as sp
from dataclasses import fields
from typing import TypeVar, Any, cast

T = TypeVar("T", bound=type)


def matchable(cls: T) -> T:
    cls_any = cast(Any, cls)
    setattr(cls_any, "__match_args__", tuple(f.name for f in fields(cls)))
    return cls


def run_and_capture(cmd: list[str], output=True) -> str:
    out = []
    with sp.Popen(
        cmd, stdout=sp.PIPE, stderr=sp.STDOUT, text=True, bufsize=1
    ) as process:
        if process.stdout is None:
            raise RuntimeError("Process stdout is None")
        for line in process.stdout:
            # Filter out nuXmv copyright output
            if line.startswith("*** ") or line.strip() == "":
                continue
            if output:
                print(line, end="")
            out.append(line)
        process.wait()
    if output:
        print()
    return "".join(out)
