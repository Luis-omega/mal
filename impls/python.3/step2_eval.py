from __future__ import annotations

from dataclasses import dataclass
from parser import TransformLisP, grammar
from typing import MutableMapping

from env import Environment, SymbolNotFound
from lark import Lark, UnexpectedInput, UnexpectedToken
from lark.exceptions import VisitError
from mal_types import (ExpressionT, FalseV, HashMap, Keyword, List,
                       MalException, Nil, NonFunctionFormAtFirstListITem,
                       Number, Pretty, PrimitiveFunction, String, Symbol,
                       TrueV, UnbalancedString, Vector, Visitor)


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


@dataclass
class Evaluator(Visitor[ExpressionT]):
    env: Environment

    def visit_symbol(self, s: Symbol) -> ExpressionT:
        result = self.env.data.get(s.symbol, None)
        if result is None:
            raise SymbolNotFound(s, self.env)
        return result

    def visit_keyword(self, k: Keyword) -> ExpressionT:
        return k

    def visit_number(self, n: Number) -> ExpressionT:
        return n

    def visit_true(self, t: TrueV) -> ExpressionT:
        return t

    def visit_false(self, f: FalseV) -> ExpressionT:
        return f

    def visit_nil(self, n: Nil) -> ExpressionT:
        return n

    def visit_string(self, st: String) -> ExpressionT:
        return st

    def visit_list(self, ls: List) -> ExpressionT:
        if ls.value:
            evaluated = [exp.visit(self) for exp in ls.value]
            f = evaluated[0]
            arguments = evaluated[1:]
            match f:
                case PrimitiveFunction(g):
                    return g(arguments)
                case _:
                    raise NonFunctionFormAtFirstListITem(ls, f, arguments)
        else:
            return ls

    def visit_vector(self, v: Vector) -> ExpressionT:
        if v.value:
            return Vector([exp.visit(self) for exp in v.value])
        else:
            return v

    def visit_hash_map(self, h: HashMap) -> ExpressionT:
        if h.value:
            return HashMap(dict((k, v.visit(self)) for k, v in h.value.items()))
        else:
            return h

    def visit_primitive_function(self, f: PrimitiveFunction) -> ExpressionT:
        return f


def eval_mal(exp: ExpressionT, evaluator: Evaluator) -> ExpressionT:
    return exp.visit(evaluator)


def print_mal(exp: ExpressionT) -> str:
    return exp.visit(Pretty())


def rep(
    parser: Lark, transformer: TransformLisP, text: str, evaluator: Evaluator
) -> str:
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
        return "mal exception: " + repr(r)
    try:
        e = eval_mal(r, evaluator)
    except MalException as ex:
        return repr(ex)
    p = print_mal(e)
    return p


def main() -> None:
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
    default_env_dict: MutableMapping[str, ExpressionT] = {
        "+": PrimitiveFunction(lambda t: Number(t[0].value + t[1].value)),
        "-": PrimitiveFunction(lambda t: Number(t[0].value - t[1].value)),
        "/": PrimitiveFunction(lambda t: Number(t[0].value / t[1].value)),
        "*": PrimitiveFunction(lambda t: Number(t[0].value * t[1].value)),
        "%": PrimitiveFunction(lambda t: Number(t[0].value % t[1].value)),
    }
    default_env: Environment = Environment(None)
    default_env.data = default_env_dict
    default_evaluator: Evaluator = Evaluator(default_env)
    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue
        result = rep(parser, transformer, text, default_evaluator)
        print(result)


if __name__ == "__main__":
    main()
