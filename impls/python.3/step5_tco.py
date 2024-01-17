from __future__ import annotations

import readline
from dataclasses import dataclass
from parser import TransformLisP, grammar

from core import get_namespace
from lark import Lark, UnexpectedInput, UnexpectedToken
from lark.exceptions import VisitError
from mal_types import (Environment, ExpressionT, FalseV, Function,
                       FunctionDefinition, HashMap, Keyword, List,
                       MalException, Nil, NonFunctionFormAtFirstListITem,
                       Number, Pretty, String, Symbol, TrueV, UnbalancedString,
                       Vector)


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

    def __str__(self):
        p = Pretty()
        return (
            "Error! bad number of arguments for:\n"
            + self.head.visit(p)
            + "\nIn expression: \n"
            + self.expression.visit(p)
        )


@dataclass
class BadNumberOfAssignations(MalException):
    head: ExpressionT
    expression: List

    def __str__(self):
        p = Pretty()
        return (
            "Error! expected a list or a vector of assignations, got:\n"
            + self.expression.value[1:].visit(p)
            + "\nIn let expression: \n"
            + self.expression.visit(p)
        )


@dataclass
class NotAssignationInLet(MalException):
    expression: ExpressionT

    def __str__(self):
        p = Pretty()
        return (
            "Error! expected symbol inside let, found:\n"
            + self.non_symbol.visit(p)
            + "\nIn: \n"
            + self.let_expression.visit(p)
        )


@dataclass
class ExpectedSymbolInLetDefinition(MalException):
    non_symbol: ExpressionT
    let_expression: ExpressionT

    def __str__(self):
        p = Pretty()
        return (
            "Error! expected symbol inside let, found:\n"
            + self.non_symbol.visit(p)
            + "\nIn: \n"
            + self.let_expression.visit(p)
        )


@dataclass
class EmptyDoBlock(MalException):
    expression: ExpressionT

    def __str__(self):
        return "Error! empty do block: " + self.expression.visit(Pretty())


@dataclass
class NonSymbolInBinding(MalException):
    non_symbol: ExpressionT
    expression: ExpressionT

    def __str__(self):
        p = Pretty()
        return (
            "Error! expected symbol, found:\n"
            + self.non_symbol.visit(p)
            + "\nIn: \n"
            + self.expression.visit(p)
        )


@dataclass
class ExpectedListOfBindings(MalException):
    expression: ExpressionT

    def __str__(self):
        return (
            "Error! expected a non empty list of bindings, got: "
            + self.expression.visit(Pretty())
        )


def eval_ast(ast: ExpressionT, env: Environment) -> ExpressionT:
    while True:
        match ast:
            case Symbol():
                return env.get(ast)
            case Keyword() | Number() | TrueV() | FalseV() | Nil() | String():
                return ast
            case List():
                if not ast.value:
                    return ast
                f = ast.value[0]
                match f:
                    case Symbol(symbol="def!"):
                        if len(ast.value) != 3:
                            raise BadNumberOfArguments(f, ast)
                        key = ast.value[1]
                        if not isinstance(key, Symbol):
                            key = Symbol(repr(key))
                        value = ast.value[2]
                        evaluted_value = eval_ast(value, env)
                        return env.set(key, evaluted_value)
                    case Symbol(symbol="let*"):
                        if len(ast.value) != 3:
                            raise BadNumberOfArguments(f, ast)
                        bindings = ast.value[1]
                        if not isinstance(bindings, List) and not isinstance(
                            bindings, Vector
                        ):
                            raise NotAssignationInLet(ast)
                        if len(bindings.value) % 2 != 0:
                            raise BadNumberOfAssignations(f, ast)

                        env = Environment(env)
                        for i in range(0, len(bindings.value), 2):
                            symbol = bindings.value[i]
                            if not isinstance(symbol, Symbol):
                                raise ExpectedSymbolInLetDefinition(symbol, ast)
                            env.set(
                                symbol,
                                eval_ast(bindings.value[i + 1], env),
                            )
                        ast = ast.value[2]
                        continue
                    case Symbol(symbol="do"):
                        remain = ast.value[1:]
                        if not remain:
                            raise EmptyDoBlock(ast)
                        for exp in remain[:-1]:
                            eval_ast(exp, env)
                        ast = remain[-1]
                        continue
                    case Symbol(symbol="if"):
                        if len(ast.value) == 4:
                            _, condition, then, _else = ast.value
                            if eval_ast(condition, env):
                                ast = then
                            else:
                                ast = _else
                            continue
                        elif len(ast.value) == 3:
                            _, condition, then = ast.value
                            if eval_ast(condition, env):
                                ast = then
                                continue
                            return Nil()
                        else:
                            raise BadNumberOfArguments(ast.value[0], ast)

                    case Symbol(symbol="fn*"):
                        if len(ast.value) != 3:
                            raise BadNumberOfArguments(ast.value[0], ast)
                        bindss = ast.value[1]
                        binds = []
                        if not isinstance(bindss, List) and not isinstance(
                            bindss, Vector
                        ):
                            raise ExpectedListOfBindings(bindss)
                        for elem in bindss.value:
                            if not isinstance(elem, Symbol):
                                raise NonSymbolInBinding(elem, ast)
                            # The copy of the list is only for mypy
                            binds.append(elem)

                        current_ast = ast

                        def closure(args: list[ExpressionT]) -> ExpressionT:
                            new_env = Environment(env, binds=binds, expressions=args)
                            return eval_ast(current_ast.value[2], new_env)

                        return FunctionDefinition(
                            binds, ast.value[2], env, Function(closure)
                        )

                    case _:
                        f = eval_ast(f, env)
                        match f:
                            case Function(g):
                                arguments = [
                                    eval_ast(exp, env) for exp in ast.value[1:]
                                ]
                                return g(arguments)
                            case FunctionDefinition(params, body, old_env, closure):
                                if len(params) != len(ast.value[1:]):
                                    raise BadNumberOfArguments(f, ast)
                                arguments = [
                                    eval_ast(exp, env) for exp in ast.value[1:]
                                ]
                                env = Environment(
                                    old_env, binds=params, expressions=arguments
                                )
                                ast = body
                                continue

                            case _:
                                raise NonFunctionFormAtFirstListITem(
                                    ast, f, ast.value[1:]
                                )

            case Vector(value):
                if value:
                    return Vector([eval_ast(exp, env) for exp in value])
                else:
                    return ast

            case HashMap(value):
                if value:
                    return HashMap(
                        dict((k, eval_ast(v, env)) for k, v in value.items())
                    )
                else:
                    return ast
            case Function() | FunctionDefinition():
                return ast


def eval_mal(exp: ExpressionT, env: Environment) -> ExpressionT:
    return eval_ast(exp, env)


def print_mal(exp: ExpressionT) -> str:
    return exp.visit(Pretty())


def rep(parser: Lark, transformer: TransformLisP, text: str, env: Environment) -> str:
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
        e = eval_mal(r, env)
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
    # inject the not function, this is required by the tutorial XD
    rep(parser, transformer, "(def! not (fn* (a) (if a false true)))", default_env)
    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue
        result = rep(parser, transformer, text, default_env)
        print(result)


if __name__ == "__main__":
    main()
