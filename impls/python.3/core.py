from dataclasses import dataclass
from typing import MutableMapping

from mal_types import (ExpressionT, FalseV, Function, List, MalException, Nil,
                       Number, Pretty, TrueV, Vector)


@dataclass
class UnexpectedArgument(MalException):
    argument: ExpressionT
    msg: str

    def __str__(self):
        p = Pretty()
        return f"Unexpected argument {self.argument.visit(p)}, expected " + self.msg


@dataclass
class UnexpectedNumberOfArguments(MalException):
    name: str
    expected: int

    def __str__(self):
        return f"Error! bad number of arguments at {self.name} expected {self.expected}"


def assert_number(x: ExpressionT) -> Number:
    if not isinstance(x, Number):
        raise UnexpectedArgument(x, " a number")
    return x


def assert_sequence(x: ExpressionT) -> List | Vector:
    if not isinstance(x, List) and not isinstance(x, Vector):
        raise UnexpectedArgument(x, " a list")
    return x


def assert_argument_number(x: list[ExpressionT], n: int, name: str) -> None:
    if len(x) != n:
        raise UnexpectedNumberOfArguments(name, n)
    return None


def bool_to_mal_bool(x: bool):
    return TrueV() if x else FalseV()


def prn(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 1, "prn")
    p = Pretty()
    print(args[0].visit(p))
    return Nil()


def _list(args: list[ExpressionT]) -> ExpressionT:
    return List(args)


def is_list(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 1, "list?")
    return bool_to_mal_bool(isinstance(args[0], List))


def is_empty(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 1, "empty?")
    ls = assert_sequence(args[0])
    return bool_to_mal_bool(not bool(ls.value))


def count(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 1, "count")
    if isinstance(args[0], Nil):
        return Number(0)
    ls = assert_sequence(args[0])
    return Number(len(ls.value))


def eq(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 2, "(=)")
    if not isinstance(args[0], type(args[1])):
        return FalseV()
    if args[0] == args[1]:
        return TrueV()
    return FalseV()


def le(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 2, "(<)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value < b.value)


def leq(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 2, "(<=)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value <= b.value)


def gt(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 2, "(>)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value > b.value)


def geq(args: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(args, 2, "(>=)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value >= b.value)


def get_namespace() -> MutableMapping[str, ExpressionT]:
    return {
        "+": Function(lambda t: Number(t[0].value + t[1].value)),
        "-": Function(lambda t: Number(t[0].value - t[1].value)),
        "/": Function(lambda t: Number(t[0].value / t[1].value)),
        "*": Function(lambda t: Number(t[0].value * t[1].value)),
        "%": Function(lambda t: Number(t[0].value % t[1].value)),
        "prn": Function(prn),
        "list": Function(_list),
        "list?": Function(is_list),
        "empty?": Function(is_empty),
        "count": Function(count),
        "=": Function(eq),
        "<": Function(le),
        "<=": Function(leq),
        ">": Function(gt),
        ">=": Function(geq),
    }
