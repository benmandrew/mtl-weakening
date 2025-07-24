from lark import Discard, Lark, Transformer

from src import ltl, marking, mitl


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
    formula = mitl.Not(mitl.Always(mitl.Eventually(mitl.Prop("p"), (0, 2))))
    trace = marking.Trace(
        [
            {"p": False},
            {"p": False},
            {"p": True},
        ],
        0,
    )
    markings = marking.Marking(trace, formula)
    formula = mitl.Not(mitl.Always(mitl.Eventually(mitl.Prop("p"), (0, 1))))
    markings[formula]
    print(markings)
    # w = weaken.Weaken(formula, indices, trace).weaken()


if __name__ == "__main__":
    main()
