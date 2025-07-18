from lark import Discard, Lark, Transformer

from src import ltl, marking, mitl

# from src import util
# import subprocess as sp
# import pprint


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


with open("res/check_model.lark") as f:
    parser = Lark(f.read(), parser="lalr")

mitl_fmla = mitl.Always(mitl.Eventually(mitl.Prop("trigger"), (0, 4)))
mitl_string = mitl.to_string(mitl_fmla)
ltlspec = ltl.to_nuxmv(mitl.mitl_to_ltl(mitl_fmla))


def sed_escape(s: str) -> str:
    return s.replace("&", r"\&")


def main():
    # with open("res/check_model.txt", "w") as f:
    #     sp.run(
    #         [
    #             "sed",
    #             "s/$LTLSPEC/{}/".format(sed_escape(ltlspec)),
    #             "res/check_model.in.txt",
    #         ],
    #         stdout=f,
    #     )
    # out = util.run_and_capture(
    #     ["nuXmv", "-source", "res/check_model.txt"], output=False
    # )
    # cex_match_string = "Trace Type: Counterexample"
    # if out.find(cex_match_string) == -1:
    #     print(f"Specification {mitl_string} is true")
    # else:
    #     out = out.split(cex_match_string)[2].strip() + "\n"
    #     parsetree = parser.parse(out)
    #     cex: marking.Trace = TreeTransformer().transform(parsetree)
    #     print(f"Counterexample to {mitl_string}:")
    #     pprint.pp(cex.trace)
    #     print()
    #     for i in range(1, 7):
    #         mitl_fmla = mitl.Always(mitl.Eventually(mitl.Prop("trigger"), (0, i)))
    #         markings = marking.Marking(cex, mitl_fmla)
    #         print(markings)
    # formula = mitl.Always(mitl.Eventually(mitl.Prop("a"), (0, 1)))
    trace = marking.Trace(
        [
            {"a": True, "b": False},
            {"a": True, "b": False},
            {"a": True, "b": False},
            {"a": False, "b": False},
            {"a": False, "b": False},
            {"a": False, "b": False},
            {"a": False, "b": False},
            {"a": False, "b": True},
        ],
        0,
    )
    # print(marking.Marking(trace, formula))
    for i in range(4, 0, -1):
        mitl_fmla = mitl.Until(
            mitl.Prop("a"), mitl.Eventually(mitl.Prop("b"), (0, i))
        )
        markings = marking.Marking(trace, mitl_fmla)
        print(markings)


if __name__ == "__main__":
    main()
