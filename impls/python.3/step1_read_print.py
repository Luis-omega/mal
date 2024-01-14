from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

from lark import (Lark, Token, Transformer, UnexpectedInput, UnexpectedToken,
                  v_args)
from lark.exceptions import VisitError

T = TypeVar("T")

grammar = """

SPACES : /\s|,/

%ignore SPACES

COMMENT : /;.*/

%ignore COMMENT

LBRACE : "{"
RBRACE : "}"
LPAREN : "("
RPAREN : ")"
LBRACKET : "["
RBRACKET : "]"

SPECIAL: "~@"
SINGLE_QUOTE : "'"
BACKTICK : "`"
TILDE : "~"
HAT: "^"
AT : "@"

STRING_COMMON : "\\\"" (/\\\\.|[^"\\\\]/)*  

STRING : STRING_COMMON "\\\""

UNBALANCED_STRING: STRING_COMMON /$/



NUMBER: /-?[1-9][0-9]*|0+/

TRUE : "True"
FALSE : "False"
NIL: "nil"

SYMBOL.-1 : /[^\s\[\]{}('"`,;)]+/
KEYWORD : ":" SYMBOL 


atom : TRUE | FALSE | NIL | NUMBER | KEYWORD | SYMBOL | STRING | UNBALANCED_STRING
    | quote
    | quasiquote
    | unquote
    | splice_unquote
    | deref
    | meta

quote : SINGLE_QUOTE expression

quasiquote : BACKTICK expression

unquote : TILDE expression

splice_unquote : SPECIAL expression

deref : AT expression

meta : HAT expression expression

list_items : expression+

list : LPAREN list_items RPAREN -> list1
    | LPAREN RPAREN -> list2

vector : LBRACKET list_items RBRACKET-> vector1
    | LBRACKET RBRACKET -> vector2

hash_map_item : STRING  expression
    | KEYWORD expression

hash_map_items : hash_map_item+

hash_map: LBRACE hash_map_items RBRACE -> hash_map1
    | LBRACE RBRACE -> hash_map2

expression : atom
    |list 
    | vector
    | hash_map

"""


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


@v_args(inline=True)
class TransformLisP(Transformer):
    @staticmethod
    def SYMBOL(token: Token) -> Symbol:
        return Symbol(token.value)

    @staticmethod
    def KEYWORD(token: Token) -> Keyword:
        return Keyword(token.value[1:])

    @staticmethod
    def NUMBER(token: Token) -> Number:
        return Number(int(token.value))

    @staticmethod
    def TRUE(token: Token) -> TrueV:
        return TrueV()

    @staticmethod
    def FALSE(token: Token) -> FalseV:
        return FalseV()

    @staticmethod
    def NIL(token: Token) -> Nil:
        return Nil()

    @staticmethod
    def STRING(token: Token) -> String:
        # TODO: Transform "\\" in "\" , "\n" in linebreak, "\"" in '"'
        # NOTE: a '\' followed by nothing else is discarted (see others mal implementations)
        return String(token.value[1:-1])

    @staticmethod
    def UNBALANCED_STRING(token: Token) -> String:
        raise UnbalancedString()

    @staticmethod
    def atom(value: ExpressionT) -> ExpressionT:
        return value

    @staticmethod
    def quote(single_quote: Token, exp: ExpressionT) -> ExpressionT:
        return List([Symbol("quote"), exp])

    @staticmethod
    def quasiquote(backtick: Token, exp: ExpressionT) -> ExpressionT:
        return List([Symbol("quasiquote"), exp])

    @staticmethod
    def unquote(tilde: Token, exp: ExpressionT) -> ExpressionT:
        return List([Symbol("unquote"), exp])

    @staticmethod
    def splice_unquote(special: Token, exp: ExpressionT) -> ExpressionT:
        return List([Symbol("splice-unquote"), exp])

    @staticmethod
    def deref(at: Token, exp: ExpressionT) -> ExpressionT:
        return List([Symbol("deref"), exp])

    @staticmethod
    def meta(hat: Token, exp1: ExpressionT, exp2: ExpressionT) -> ExpressionT:
        return List([Symbol("with-meta"), exp2, exp1])

    @staticmethod
    def list_items(*items: ExpressionT) -> list[ExpressionT]:
        return list(items)

    @staticmethod
    def list1(lparen: Token, list_items: list[ExpressionT], rparen: Token) -> List:
        return List(list_items)

    @staticmethod
    def list2(lparen: Token, rparen: Token) -> ExpressionT:
        return List([])

    @staticmethod
    def vector1(
        lbracket: Token, list_items: list[ExpressionT], rbracket: Token
    ) -> Vector:
        return Vector(list_items)

    @staticmethod
    def vector2(lbracket: Token, rbracket: Token) -> Vector:
        return Vector([])

    @staticmethod
    def hash_map_item(
        key: Union[String, Keyword], exp: ExpressionT
    ) -> tuple[Union[String, Keyword], ExpressionT]:
        return (key, exp)

    @staticmethod
    def hash_map_items(
        *v: tuple[Union[String, Keyword], ExpressionT]
    ) -> list[tuple[Union[String, Keyword], ExpressionT]]:
        return list(v)

    @staticmethod
    def hash_map1(
        lbracket: Token,
        hash_items: list[tuple[Union[String, Keyword], ExpressionT]],
        rbracket: Token,
    ) -> HashMap:
        acc = dict()
        for key, value in hash_items:
            print(key, value)
            acc[key] = value
        return HashMap(acc)

    @staticmethod
    def hash_map2(lbracket: Token, rbracket: Token) -> HashMap:
        return HashMap(dict())

    @staticmethod
    def expression(exp: ExpressionT) -> ExpressionT:
        return exp


def read(
    parser: Lark, transformer: TransformLisP, text: str
) -> ExpressionT | UnexpectedInput | MalException:
    try:
        result = parser.parse(text)
    except UnexpectedInput as e:
        return e
    try:
        transformed = transformer.transform(result)
        return transformed
    except VisitError as e:
        if e.rule == "UNBALANCED_STRING":
            return UnbalancedString()
        print(repr(e))
        return MalException()


def eval_mal(exp: ExpressionT) -> ExpressionT:
    return exp


def print_mal(exp: ExpressionT) -> str:
    return exp.visit(Pretty())


def rep(parser: Lark, transformer: TransformLisP, text: str) -> str:
    r = read(parser, transformer, text)
    if isinstance(r, UnexpectedInput):
        if isinstance(r, UnexpectedToken):
            print("unexpected token")
            if r.token.type == "$END":
                return "EOF"
            return str(r)
        return str(type(r)) + str(r)
    elif isinstance(r, UnbalancedString):
        return "unbalanced"
    elif isinstance(r, MalException):
        return "mal exception"
    e = eval_mal(r)
    p = print_mal(e)
    return p


def main():
    parser = Lark(
        grammar,
        debug=True,
        cache=None,
        maybe_placeholders=True,
        keep_all_tokens=True,
        parser="lalr",
        lexer="basic",
        start=["expression"],
    )
    transformer = TransformLisP()
    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        result = rep(parser, transformer, text)
        print(result)


if __name__ == "__main__":
    main()
