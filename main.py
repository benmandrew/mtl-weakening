import subprocess as sp
from lark import Lark, Transformer, Discard
import ltl
import mitl
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

    def state(self, tok):
        expr = list(filter(lambda x: type(x) is not int, tok))
        d = {}
        for e in expr:
            k, v = e.children
            d[k] = v
        return d


with open("cex.lark", "r") as f:
    parser = Lark(f.read(), parser="lalr")

# ltlspec = "G(trigger -> counter=N + 1)"

mitl_fmla = mitl.Always(
    mitl.Eventually(mitl.Prop("trigger"), (0, 4)), (0, None)
)
mitl_string = mitl.to_string(mitl_fmla)
ltlspec = ltl.to_nuxmv(mitl.mitl_to_ltl(mitl_fmla))


def sed_escape(s):
    return s.replace("&", "\&")


def run_and_capture(cmd):
    process = sp.Popen(
        cmd, stdout=sp.PIPE, stderr=sp.STDOUT, text=True, bufsize=1
    )
    out = []
    for line in process.stdout:
        # Ignore nuXmv copyright output
        if not line.startswith("*** ") and line != "\n":
            print(line, end="")
            out.append(line)
    process.wait()
    print()
    return "".join(out)


def main():
    f = open("commands.txt", "w")
    sp.run(
        [
            "sed",
            "s/$LTLSPEC/{}/".format(sed_escape(ltlspec)),
            "commands.in.txt",
        ],
        stdout=f,
    )
    out = run_and_capture(["nuXmv", "-source", "commands.txt"])
    cex_string = "Trace Type: Counterexample"
    if out.find(cex_string) == -1:
        print(f"Specification {mitl_string} is true")
    else:
        out = out.split(cex_string)[2].strip() + "\n"
        out = parser.parse(out)
        out = TreeTransformer().transform(out)
        print(f"Counterexample to {mitl_string}:")
        pprint.pp(out)


if __name__ == "__main__":
    main()
