from dataclasses import dataclass
from typing import MutableMapping, Optional

from mal_types import ExpressionT, List, MalException, Symbol


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
