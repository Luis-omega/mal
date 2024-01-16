from dataclasses import dataclass
from typing import MutableMapping

from mal_types import (ExpressionT, FalseV, Function, List, MalException, Nil,
                       Number, Pretty, String, TrueV, Vector)


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


def prn(args: list[ExpressionT]) -> Nil:
    print(pr_str(args).value)
    return Nil()


def _list(args: list[ExpressionT]) -> List:
    return List(args)


def is_list(args: list[ExpressionT]) -> TrueV | FalseV:
    assert_argument_number(args, 1, "list?")
    return bool_to_mal_bool(isinstance(args[0], List))


def is_empty(args: list[ExpressionT]) -> TrueV | FalseV:
    assert_argument_number(args, 1, "empty?")
    ls = assert_sequence(args[0])
    return bool_to_mal_bool(not bool(ls.value))


def count(args: list[ExpressionT]) -> Number:
    assert_argument_number(args, 1, "count")
    if isinstance(args[0], Nil):
        return Number(0)
    ls = assert_sequence(args[0])
    return Number(len(ls.value))


def eq(args: list[ExpressionT]) -> TrueV | FalseV:
    assert_argument_number(args, 2, "(=)")
    x = args[0]
    y = args[1]
    # TODO: WHY??? WHY???Y WHY have vectors if
    # mal doesn't make a distintion between vectors and list?
    if isinstance(x, List) or isinstance(x, Vector):
        if isinstance(y, List) or isinstance(y, Vector):
            return bool_to_mal_bool(
                len(x.value) == len(y.value)
                and all(eq([x1, y1]) for x1, y1 in zip(x.value, y.value))
            )
    if not isinstance(args[0], type(args[1])):
        return FalseV()
    if args[0] == args[1]:
        return TrueV()
    return FalseV()


def le(args: list[ExpressionT]) -> TrueV | FalseV:
    assert_argument_number(args, 2, "(<)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value < b.value)


def leq(args: list[ExpressionT]) -> TrueV | FalseV:
    assert_argument_number(args, 2, "(<=)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value <= b.value)


def gt(args: list[ExpressionT]) -> TrueV | FalseV:
    assert_argument_number(args, 2, "(>)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value > b.value)


def geq(args: list[ExpressionT]) -> TrueV | FalseV:
    assert_argument_number(args, 2, "(>=)")
    a = assert_number(args[0])
    b = assert_number(args[1])
    return bool_to_mal_bool(a.value >= b.value)


def pr_str(args: list[ExpressionT]) -> String:
    p = Pretty()
    return String(" ".join(x.visit(p) for x in args))


def mal_str(args: list[ExpressionT]) -> String:
    p = Pretty(False)
    return String("".join(x.visit(p) for x in args))


def println(args: list[ExpressionT]) -> Nil:
    p = Pretty(False)
    result = " ".join(x.visit(p) for x in args)
    print(result)
    return Nil()


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
        "pr-str": Function(pr_str),
        "str": Function(mal_str),
        "println": Function(println),
    }
