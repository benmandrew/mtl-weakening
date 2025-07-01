import subprocess as sp
from lark import Lark, Transformer, Discard


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

ltlspec = "G(trigger -> counter=N + 1)"


def main():
    f = open("commands.txt", "w")
    sp.run(
        ["sed", "s/$LTLSPEC/{}/".format(ltlspec), "commands.in.txt"], stdout=f
    )
    out = sp.run(
        ["nuXmv", "-source", "commands.txt"], capture_output=True, text=True
    ).stdout
    out = out.split("Trace Type: Counterexample")[2].strip() + "\n"
    out = parser.parse(out)
    out = TreeTransformer().transform(out)
    print(out)


if __name__ == "__main__":
    main()
