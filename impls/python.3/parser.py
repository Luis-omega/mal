from typing import Union

from lark import Token, Transformer, v_args
from mal_types import (ExpressionT, FalseV, HashMap, Keyword, List, Nil,
                       Number, String, Symbol, TrueV, Vector)

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
