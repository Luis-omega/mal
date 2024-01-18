from __future__ import annotations

import readline
import sys
from dataclasses import dataclass
from parser import parse_str

from core import assert_argument_number, get_namespace
from mal_types import (Environment, ExpressionT, FalseV, Function,
                       FunctionDefinition, HashMap, Keyword, List,
                       MalException, Nil, NonFunctionFormAtFirstListITem,
                       Number, Pretty, String, Symbol, TrueV, Vector)


def read(text: str) -> ExpressionT | str:
    return parse_str(text)


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


def mal_eval(x: list[ExpressionT], env: Environment) -> ExpressionT:
    assert_argument_number(x, 1, "eval")
    ast = x[0]
    return eval_ast(ast, env)


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


def rep(text: str, env: Environment) -> str:
    r = read(text)
    if isinstance(r, str):
        return r
    try:
        e = eval_mal(r, env)
    except MalException as ex:
        return str(ex)
    p = print_mal(e)
    return p


def main() -> None:
    mal_argv = List([String(x) for x in sys.argv[2:]])
    default_env_dict = get_namespace()
    default_env: Environment = Environment(None)
    default_env.data = default_env_dict
    default_env.set(Symbol("*ARGV*"), mal_argv)
    # inject the not function, this is required by the tutorial XD
    rep("(def! not (fn* (a) (if a false true)))", default_env)
    rep(
        """(def! load-file (fn* (f) (eval (read-string (str "(do " (slurp f) "\nnil)")))))""",
        default_env,
    )
    default_env.set(Symbol("eval"), Function(lambda x: mal_eval(x, default_env)))
    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
        rep('(load-file "' + file_path + '")', default_env)
        exit(0)

    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue
        result = rep(text, default_env)
        print(result)


if __name__ == "__main__":
    main()
