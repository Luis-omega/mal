from __future__ import annotations

import readline
from dataclasses import dataclass
from parser import parse_str

from core import get_namespace
from mal_types import (Atom, Environment, ExpressionT, FalseV, Function,
                       FunctionDefinition, HashMap, Keyword, List,
                       MalException, Nil, NonFunctionFormAtFirstListITem,
                       Number, Pretty, String, Symbol, TrueV, Vector, Visitor)


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
            case Symbol(symbol="do"):
                remain = ls.value[1:]
                if not remain:
                    raise EmptyDoBlock(ls)
                acc = remain[0]
                for exp in remain:
                    acc = exp.visit(self)
                return acc
            case Symbol(symbol="if"):
                if len(ls.value) == 4:
                    _, condition, then, _else = ls.value
                    if condition.visit(self):
                        return then.visit(self)
                    return _else.visit(self)
                elif len(ls.value) == 3:
                    _, condition, then = ls.value
                    if condition.visit(self):
                        return then.visit(self)
                    return Nil()
                else:
                    raise BadNumberOfArguments(ls.value[0], ls)

            case Symbol(symbol="fn*"):
                if len(ls.value) != 3:
                    raise BadNumberOfArguments(ls.value[0], ls)
                bindss = ls.value[1]
                binds = []
                if not isinstance(bindss, List) and not isinstance(bindss, Vector):
                    raise ExpectedListOfBindings(bindss)
                for elem in bindss.value:
                    if not isinstance(elem, Symbol):
                        raise NonSymbolInBinding(elem, ls)
                    # The copy of the list is only for mypy
                    binds.append(elem)

                def closure(args: list[ExpressionT]):
                    new_env = Environment(self.env, binds=binds, expressions=args)
                    return ls.value[2].visit(Evaluator(new_env))

                return Function(closure)

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

    def visit_function_definition(self, f: FunctionDefinition) -> ExpressionT:
        return f

    def visit_atom(self, a: Atom) -> ExpressionT:
        return a


def eval_mal(exp: ExpressionT, evaluator: Evaluator) -> ExpressionT:
    return exp.visit(evaluator)


def print_mal(exp: ExpressionT) -> str:
    return exp.visit(Pretty())


def rep(text: str, evaluator: Evaluator) -> str:
    r = read(text)
    if isinstance(r, str):
        return r
    try:
        e = eval_mal(r, evaluator)
    except MalException as ex:
        return str(ex)
    p = print_mal(e)
    return p


def main() -> None:
    default_env_dict = get_namespace()
    default_env: Environment = Environment(None)
    default_env.data = default_env_dict
    default_evaluator: Evaluator = Evaluator(default_env)
    # inject the not function, this is required by the tutorial XD
    rep("(def! not (fn* (a) (if a false true)))", default_evaluator)
    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue
        result = rep(text, default_evaluator)
        print(result)


if __name__ == "__main__":
    main()
