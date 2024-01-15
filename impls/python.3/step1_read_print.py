from __future__ import annotations

from parser import TransformLisP, grammar

from lark import Lark, UnexpectedInput, UnexpectedToken
from lark.exceptions import VisitError
from mal_types import ExpressionT, MalException, Pretty, UnbalancedString


def read(
    parser: Lark, transformer: TransformLisP, text: str
) -> ExpressionT | UnexpectedInput | MalException:
    try:
        result = parser.parse(text)
    except UnexpectedInput as e:
        return e
    try:
        transformed = transformer.transform(result)
        return transformed
    except VisitError as e:
        if e.rule == "UNBALANCED_STRING":
            return UnbalancedString()
        print(repr(e))
        return MalException()


def eval_mal(exp: ExpressionT) -> ExpressionT:
    return exp


def print_mal(exp: ExpressionT) -> str:
    return exp.visit(Pretty())


def rep(parser: Lark, transformer: TransformLisP, text: str) -> str:
    r = read(parser, transformer, text)
    if isinstance(r, UnexpectedInput):
        if isinstance(r, UnexpectedToken):
            print("unexpected token")
            if r.token.type == "$END":
                return "EOF"
            return str(r)
        return str(type(r)) + str(r)
    elif isinstance(r, UnbalancedString):
        return "unbalanced"
    elif isinstance(r, MalException):
        return "mal exception"
    e = eval_mal(r)
    p = print_mal(e)
    return p


def main():
    # We don't use the transformer inside this call to Lark
    # since we can raise exceptions from the transformer
    # and the Visitor class of Lark catch them
    parser = Lark(
        grammar,
        debug=True,
        cache=None,
        maybe_placeholders=True,
        keep_all_tokens=True,
        parser="lalr",
        lexer="basic",
        start=["expression"],
    )
    transformer = TransformLisP()
    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        result = rep(parser, transformer, text)
        print(result)


if __name__ == "__main__":
    main()
