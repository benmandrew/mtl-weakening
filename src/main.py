from lark import Lark, Transformer, Discard
from src import ltl
from src import mitl
from src import marking
from src import util
import subprocess as sp
import pprint


class TreeTransformer(Transformer):
    INT = int
    WORD = str
    true = lambda self, _: True  # noqa: E731
    false = lambda self, _: False  # noqa: E731
    NL = lambda self, _: Discard  # noqa: E731

    def start(self, tok):
        return marking.Trace(tok)

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

mitl_fmla = mitl.Always(mitl.Eventually(mitl.Prop("trigger"), (0, 4)))
mitl_string = mitl.to_string(mitl_fmla)
ltlspec = ltl.to_nuxmv(mitl.mitl_to_ltl(mitl_fmla))


def sed_escape(s: str) -> str:
    return s.replace("&", "\&")


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
    out = util.run_and_capture(
        ["nuXmv", "-source", "res/check_model.txt"], output=False
    )
    cex_match_string = "Trace Type: Counterexample"
    if out.find(cex_match_string) == -1:
        print(f"Specification {mitl_string} is true")
    else:
        out = out.split(cex_match_string)[2].strip() + "\n"
        parsetree = parser.parse(out)
        cex: marking.Trace = TreeTransformer().transform(parsetree)
        print(f"Counterexample to {mitl_string}:")
        pprint.pp(cex.trace)
        print()
        markings = marking.Marking(cex, mitl_fmla)
        print(markings)


if __name__ == "__main__":
    main()
