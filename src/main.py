import subprocess as sp
from lark import Lark, Transformer, Discard
import ltl
import mitl
import marking
import pprint


class TreeTransformer(Transformer):
    INT = int
    WORD = str
    true = lambda self, _: True  # noqa: E731
    false = lambda self, _: False  # noqa: E731
    NL = lambda self, _: Discard  # noqa: E731

    def start(self, tok):
        return tok

    def expr(self, tok):
        return tok[0]

    def state(self, tok) -> dict:
        expr = list(filter(lambda x: type(x) is not int, tok))
        d = {}
        for e in expr:
            k, v = e.children
            d[k] = v
        return d


with open("res/check_model.lark", "r") as f:
    parser = Lark(f.read(), parser="lalr")

mitl_fmla = mitl.Always(
    mitl.Eventually(mitl.Prop("trigger"), (0, 4)), (0, None)
)
mitl_string = mitl.to_string(mitl_fmla)
ltlspec = ltl.to_nuxmv(mitl.mitl_to_ltl(mitl_fmla))


def sed_escape(s: str) -> str:
    return s.replace("&", "\&")


def run_and_capture(cmd, output=True) -> str:
    process = sp.Popen(
        cmd, stdout=sp.PIPE, stderr=sp.STDOUT, text=True, bufsize=1
    )
    out = []
    if process.stdout is None:
        raise ValueError("stdout is None")
    for line in process.stdout:
        # Ignore nuXmv copyright output
        if not line.startswith("*** ") and line != "\n":
            if output:
                print(line, end="")
            out.append(line)
    process.wait()
    if output:
        print()
    return "".join(out)


def main():
    with open("res/check_model.txt", "w") as f:
        sp.run(
            [
                "sed",
                "s/$LTLSPEC/{}/".format(sed_escape(ltlspec)),
                "res/check_model.in.txt",
            ],
            stdout=f,
        )
    out = run_and_capture(
        ["nuXmv", "-source", "res/check_model.txt"], output=False
    )
    cex_match_string = "Trace Type: Counterexample"
    if out.find(cex_match_string) == -1:
        print(f"Specification {mitl_string} is true")
    else:
        out = out.split(cex_match_string)[2].strip() + "\n"
        parsetree = parser.parse(out)
        cex: list[dict[str, bool | int]] = TreeTransformer().transform(
            parsetree
        )
        print(f"Counterexample to {mitl_string}:")
        pprint.pp(cex)
        print()

        subformulae = marking.write_trace_smv("res/trace.smv", cex, mitl_fmla)

        out = run_and_capture(
            ["nuXmv", "-source", "res/check_trace.txt"], output=False
        )

        markings = marking.parse_nuxmv_output(out, subformulae, len(cex))
        # print(markings)

        print(marking.fmt_markings(markings))


if __name__ == "__main__":
    main()
