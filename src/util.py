import subprocess as sp


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
