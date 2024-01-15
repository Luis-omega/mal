from dataclasses import dataclass
from typing import MutableMapping, Optional

from mal_types import ExpressionT, MalException, Symbol


@dataclass
class Environment:
    data: MutableMapping[str, ExpressionT]
    outer: Optional["Environment"]

    def __init__(self, outer: Optional["Environment"]) -> None:
        self.data = dict()
        self.outer = outer

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
