from __future__ import annotations

from dataclasses import dataclass
from parser import parse_str

from core import get_namespace
from mal_types import (Atom, Environment, ExpressionT, FalseV, Function,
                       FunctionDefinition, HashMap, Keyword, List,
                       MalException, Nil, NonFunctionFormAtFirstListITem,
                       Number, Pretty, String, Symbol, SymbolNotFound, TrueV,
                       Vector, Visitor)


def read(text: str) -> ExpressionT | str:
    return parse_str(text)


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
                case Function(g):
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
        return repr(ex)
    p = print_mal(e)
    return p


def main() -> None:
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
        result = rep(text, default_evaluator)
        print(result)


if __name__ == "__main__":
    main()
