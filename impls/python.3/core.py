from dataclasses import dataclass
from parser import parse_str
from typing import MutableMapping, TypeVar

from mal_types import (Atom, Expression, ExpressionT, FalseV, Function,
                       FunctionDefinition, List, MalException, Nil, Number,
                       Pretty, String, TrueV, Vector)

T = TypeVar("T", bound=Expression)


@dataclass
class UnexpectedArgument(MalException):
    argument: ExpressionT
    msg: str

    def __str__(self):
        p = Pretty()
        return (
            f"Error! Unexpected argument {self.argument.visit(p)}, expected " + self.msg
        )


@dataclass
class UnexpectedNumberOfArguments(MalException):
    name: str
    expected: int

    def __str__(self):
        return f"Error! bad number of arguments at {self.name} expected {self.expected}"


@dataclass
class ParsingError(MalException):
    msg: str

    def __str__(self):
        return self.msg


@dataclass
class MalIOError(MalException):
    e: IOError


class CarOnEmptyList(MalException):
    def __str__(self):
        return "Error! attempt to access head element of an empty list"


class CdrOnEmptyList(MalException):
    def __str__(self):
        return "Error! attempt to access tail of an empty list"


def assert_is_of_class(x: ExpressionT, _class: type[T]) -> T:
    if not isinstance(x, _class):
        raise UnexpectedArgument(x, " a " + _class.__name__)
    return x


def assert_number(x: ExpressionT) -> Number:
    return assert_is_of_class(x, Number)


def assert_list(x: ExpressionT) -> List:
    return assert_is_of_class(x, List)


def assert_sequence(x: ExpressionT) -> List | Vector:
    if isinstance(x, List) or isinstance(x, Vector):
        return x
    raise UnexpectedArgument(x, " a sequence")


def assert_string(x: ExpressionT) -> String:
    return assert_is_of_class(x, String)


def assert_atom(x: ExpressionT) -> Atom:
    return assert_is_of_class(x, Atom)


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


def car(x: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(x, 1, "car")
    ls = assert_list(x[0])
    if ls.value:
        return ls.value[0]
    raise CarOnEmptyList()


def cdr(x: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(x, 1, "cdr")
    ls = assert_list(x[0])
    if len(ls.value) >= 1:
        return List(ls.value[1:])
    raise CdrOnEmptyList()


def read_string(x: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(x, 1, "read-string")
    s = assert_string(x[0])
    result = parse_str(s.value)
    if isinstance(result, str):
        raise ParsingError(result)
    return result


def slurp(x: list[ExpressionT]) -> String:
    assert_argument_number(x, 1, "slurp")
    s = assert_string(x[0])
    try:
        with open(s.value, "r") as f:
            content = f.read()
            return String(content)
    except IOError as e:
        raise MalIOError(e)


def atom(x: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(x, 1, "atom")
    return Atom(x[0])


def is_atom(x: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(x, 1, "atom")
    return bool_to_mal_bool(isinstance(x[0], Atom))


def deref(x: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(x, 1, "deref")
    a = assert_atom(x[0])
    return a.value


def reset(x: list[ExpressionT]) -> ExpressionT:
    assert_argument_number(x, 2, "reset")
    a = assert_atom(x[0])
    v = x[1]
    a.value = v
    return v


def swap(x: list[ExpressionT]) -> ExpressionT:
    if len(x) < 2:
        # TODO: replace this with a more acurate exception
        raise UnexpectedNumberOfArguments("swap", 2)
    a = assert_atom(x[0])
    args = x[2:]
    f = x[1]

    if isinstance(f, Function):
        a.value = f.value([a.value] + args)
        return a.value
    if isinstance(f, FunctionDefinition):
        a.value = f.closure.value([a.value] + args)
        return a.value
    raise UnexpectedArgument(x[1], "a function")


def get_namespace() -> MutableMapping[str, ExpressionT]:
    return {
        "+": Function(
            lambda t: Number(assert_number(t[0]).value + assert_number(t[1]).value)
        ),
        "-": Function(
            lambda t: Number(assert_number(t[0]).value - assert_number(t[1]).value)
        ),
        "/": Function(
            lambda t: Number(assert_number(t[0]).value // assert_number(t[1]).value)
        ),
        "*": Function(
            lambda t: Number(assert_number(t[0]).value * assert_number(t[1]).value)
        ),
        "%": Function(
            lambda t: Number(assert_number(t[0]).value % assert_number(t[1]).value)
        ),
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
        "car": Function(car),
        "cdr": Function(cdr),
        "read-string": Function(read_string),
        "slurp": Function(slurp),
        "atom": Function(atom),
        "atom?": Function(is_atom),
        "deref": Function(deref),
        "reset!": Function(reset),
        "swap!": Function(swap),
    }
