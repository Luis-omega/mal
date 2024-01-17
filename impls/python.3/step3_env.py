from __future__ import annotations

from dataclasses import dataclass
from parser import TransformLisP, grammar
from typing import MutableMapping

from core import get_namespace
from env import Environment, SymbolNotFound
from lark import Lark, UnexpectedInput, UnexpectedToken
from lark.exceptions import VisitError
from mal_types import (ExpressionT, FalseV, Function, HashMap, Keyword, List,
                       MalException, Nil, NonFunctionFormAtFirstListITem,
                       Number, Pretty, String, Symbol, TrueV, UnbalancedString,
                       Vector, Visitor)


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
class BadNumberOfArguments(MalException):
    head: ExpressionT
    expression: List


@dataclass
class BadNumberOfAssignations(MalException):
    head: ExpressionT
    expression: List


@dataclass
class NotAssignationInLet(MalException):
    expression: ExpressionT


@dataclass
class ExpectedSymbolInLetDefinition(MalException):
    non_symbol: ExpressionT
    let_expression: ExpressionT


@dataclass
class Evaluator(Visitor[ExpressionT]):
    env: Environment

    def visit_symbol(self, s: Symbol) -> ExpressionT:
        return self.env.get(s)

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
        if not ls.value:
            return ls
        f = ls.value[0]
        match f:
            case Symbol(symbol="def!"):
                if len(ls.value) != 3:
                    raise BadNumberOfArguments(f, ls)
                key = ls.value[1]
                if not isinstance(key, Symbol):
                    key = Symbol(repr(key))
                value = ls.value[2]
                evaluted_value = value.visit(self)
                return self.env.set(key, evaluted_value)
            case Symbol(symbol="let*"):
                if len(ls.value) != 3:
                    raise BadNumberOfArguments(f, ls)
                bindings = ls.value[1]
                if not isinstance(bindings, List) and not isinstance(bindings, Vector):
                    raise NotAssignationInLet(ls)
                if len(bindings.value) % 2 != 0:
                    raise BadNumberOfAssignations(f, ls)

                new_env = Environment(self.env)
                new_evaluator = Evaluator(new_env)
                for i in range(0, len(bindings.value), 2):
                    symbol = bindings.value[i]
                    if not isinstance(symbol, Symbol):
                        raise ExpectedSymbolInLetDefinition(symbol, ls)
                    new_env.set(
                        symbol,
                        bindings.value[i + 1].visit(new_evaluator),
                    )

                return ls.value[2].visit(new_evaluator)
            case _:
                f = f.visit(self)
                match f:
                    case Function(g):
                        arguments = [exp.visit(self) for exp in ls.value[1:]]
                        return g(arguments)
                    case _:
                        raise NonFunctionFormAtFirstListITem(ls, f, ls.value[1:])

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

    def visit_function(self, f: Function) -> ExpressionT:
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
        return "mal exception: " + str(r)
    try:
        e = eval_mal(r, evaluator)
    except MalException as ex:
        return str(ex)
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
    default_env_dict = get_namespace()
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
