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
