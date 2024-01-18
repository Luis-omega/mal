from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, MutableMapping, Optional, TypeVar, Union

T = TypeVar("T")

ExpressionT = Union[
    "Symbol",
    "Number",
    "TrueV",
    "FalseV",
    "Nil",
    "String",
    "List",
    "Vector",
    "Keyword",
    "HashMap",
    "Function",
    "FunctionDefinition",
    "Atom",
]


class MalException(Exception):
    pass


@dataclass
class NonFunctionFormAtFirstListITem(MalException):
    exp: ExpressionT
    f: ExpressionT
    arguments: list[ExpressionT]

    def __str__(self):
        p = Pretty()
        return (
            "Error! expected a function or form as first argument, got:\n"
            + self.f.visit(p)
            + "\nIn let expression: \n"
            + List(self.arguments).visit(p)
        )


class Visitor(ABC, Generic[T]):
    @abstractmethod
    def visit_symbol(self, s: Symbol) -> T:
        pass

    @abstractmethod
    def visit_keyword(self, s: Keyword) -> T:
        pass

    @abstractmethod
    def visit_number(self, n: Number) -> T:
        pass

    @abstractmethod
    def visit_true(self, t: TrueV) -> T:
        pass

    @abstractmethod
    def visit_false(self, f: FalseV) -> T:
        pass

    @abstractmethod
    def visit_nil(self, n: Nil) -> T:
        pass

    @abstractmethod
    def visit_string(self, st: String) -> T:
        pass

    @abstractmethod
    def visit_list(self, ls: List) -> T:
        pass

    @abstractmethod
    def visit_vector(self, v: Vector) -> T:
        pass

    @abstractmethod
    def visit_hash_map(self, v: HashMap) -> T:
        pass

    @abstractmethod
    def visit_function(self, v: Function) -> T:
        pass

    @abstractmethod
    def visit_function_definition(self, v: FunctionDefinition) -> T:
        pass

    @abstractmethod
    def visit_atom(self, v: Atom) -> T:
        pass


class Expression(ABC):
    @abstractmethod
    def visit(self, visitor: Visitor[T]) -> T:
        pass


@dataclass
class Symbol(Expression):
    symbol: str

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_symbol(self)


@dataclass
class Keyword(Expression):
    value: str

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_keyword(self)

    def __hash__(self):
        return hash(repr(self))


@dataclass
class Number(Expression):
    value: int

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_number(self)


@dataclass
class TrueV(Expression):
    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_true(self)

    def __bool__(self):
        return True


@dataclass
class FalseV(Expression):
    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_false(self)

    def __bool__(self):
        return False


@dataclass
class Nil(Expression):
    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_nil(self)

    def __bool__(self):
        return False


@dataclass
class String(Expression):
    value: str

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_string(self)

    def __hash__(self):
        return hash(repr(self))


@dataclass
class List(Expression):
    value: list[ExpressionT]

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_list(self)


@dataclass
class Vector(Expression):
    value: list[ExpressionT]

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_vector(self)


@dataclass
class HashMap(Expression):
    value: dict[Union[String, Keyword], ExpressionT]

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_hash_map(self)


@dataclass
class Function(Expression):
    value: Callable[[list[ExpressionT]], ExpressionT]

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_function(self)


@dataclass
class FunctionDefinition(Expression):
    params: list[Symbol]
    body: ExpressionT
    env: Environment
    closure: Function

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_function_definition(self)


@dataclass
class Atom(Expression):
    value: ExpressionT

    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_atom(self)


class Pretty(Visitor[str]):
    print_readably: bool

    def __init__(self, print_readably: bool = True):
        self.print_readably = print_readably

    def visit_symbol(self, s: Symbol) -> str:
        return s.symbol

    def visit_keyword(self, k: Keyword) -> str:
        return ":" + k.value

    def visit_number(self, n: Number) -> str:
        return str(n.value)

    def visit_true(self, t: TrueV) -> str:
        return "true"

    def visit_false(self, f: FalseV) -> str:
        return "false"

    def visit_nil(self, n: Nil) -> str:
        return "nil"

    def visit_string(self, st: String) -> str:
        if not self.print_readably:
            return f"{st.value}"
        after_backslash = st.value.replace("\\", "\\\\")
        after_breaks = after_backslash.replace("\n", "\\n")
        final = after_breaks.replace('"', '\\"')
        return f'"{final}"'

    def visit_list(self, ls: List) -> str:
        acc = [e.visit(self) for e in ls.value]
        return "(" + " ".join(acc) + ")"

    def visit_vector(self, v: Vector) -> str:
        acc = [e.visit(self) for e in v.value]
        return "[" + " ".join(acc) + "]"

    def visit_hash_map(self, h: HashMap) -> str:
        acc = [f"{k.visit(self)} {v.visit(self)}" for k, v in h.value.items()]
        return "{" + " ".join(acc) + "}"

    def visit_function(self, fun: Function) -> str:
        return repr(fun)

    def visit_function_definition(self, fun: FunctionDefinition) -> str:
        return repr(fun)

    def visit_atom(self, a: Atom) -> str:
        if a != a.value:
            return f"(atom {a.value.visit(self)})"
        return repr(a)


@dataclass
class Environment:
    data: MutableMapping[str, ExpressionT]
    outer: Optional["Environment"]

    def __init__(
        self,
        outer: Optional["Environment"],
        binds: Optional[list[Symbol]] = None,
        expressions: Optional[list[ExpressionT]] = None,
    ) -> None:
        self.data = dict()
        self.outer = outer

        if binds is None:
            if expressions is not None:
                raise WrongNumberOfArguments(binds, expressions)
            return None

        if expressions is None:
            raise WrongNumberOfArguments(binds, expressions)

        for i in range(0, len(binds)):
            if binds[i].symbol == "&":
                self.set(binds[i + 1], List(expressions[i:]))
                return None
            else:
                self.set(binds[i], expressions[i])

    def set(self, symbol: Symbol, value: ExpressionT) -> ExpressionT:
        self.data.__setitem__(symbol.symbol, value)
        return value

    def find(self, symbol: Symbol) -> Optional[ExpressionT]:
        try:
            result = self.data.__getitem__(symbol.symbol)
        except KeyError:
            if self.outer is None:
                return None
            return self.outer.find(symbol)
        return result

    def get(self, symbol: Symbol) -> ExpressionT:
        result = self.find(symbol)
        if result is None:
            raise SymbolNotFound(symbol, self)
        return result


@dataclass
class SymbolNotFound(MalException):
    symbol: Symbol
    hash_map: Environment

    def __str__(self):
        return f"'{self.symbol.symbol}' not found in the environment: {self.hash_map}"


@dataclass
class WrongNumberOfArguments(MalException):
    symbols: Optional[list[Symbol]]
    arguments: Optional[list[ExpressionT]]
