from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")

ExpressionT = Union[
    "Symbol", "Number", "TrueV", "FalseV", "Nil", "String", "List", "Vector"
]


class MalException(Exception):
    pass


class UnbalancedString(MalException):
    pass


class Visitor(Generic[T]):
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


@dataclass
class FalseV(Expression):
    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_false(self)


@dataclass
class Nil(Expression):
    def visit(self, visitor: Visitor[T]) -> T:
        return visitor.visit_nil(self)


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


class Pretty(Visitor[str]):
    def visit_symbol(self, s: Symbol) -> str:
        return s.symbol

    def visit_keyword(self, s: Keyword) -> str:
        return ":" + s.value

    def visit_number(self, n: Number) -> str:
        return str(n.value)

    def visit_true(self, t: TrueV) -> str:
        return "True"

    def visit_false(self, f: FalseV) -> str:
        return "False"

    def visit_nil(self, n: Nil) -> str:
        return "nil"

    def visit_string(self, st: String) -> str:
        return f'"{st.value}"'

    def visit_list(self, ls: List) -> str:
        acc = [e.visit(self) for e in ls.value]
        return "(" + " ".join(acc) + ")"

    def visit_vector(self, v: Vector) -> str:
        acc = [e.visit(self) for e in v.value]
        return "[" + " ".join(acc) + "]"

    def visit_hash_map(self, h: HashMap) -> str:
        acc = [f"{k.visit(self)} {v.visit(self)}" for k, v in h.value.items()]
        return "{" + " ".join(acc) + "}"
