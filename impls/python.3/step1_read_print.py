from __future__ import annotations

from parser import parse_str

from mal_types import ExpressionT, Pretty


def read(text: str) -> ExpressionT | str:
    return parse_str(text)


def eval_mal(exp: ExpressionT) -> ExpressionT:
    return exp


def print_mal(exp: ExpressionT) -> str:
    return exp.visit(Pretty())


def rep(text: str) -> str:
    r = read(text)
    if isinstance(r, str):
        return r
    e = eval_mal(r)
    p = print_mal(e)
    return p


def main():
    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        result = rep(text)
        print(result)


if __name__ == "__main__":
    main()
