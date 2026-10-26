"""Token definitions for the Lyslyn programming language."""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Literals
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Literals Keywords
    TRUE = auto()       # true, yes
    FALSE = auto()      # false, no
    NIL = auto()        # nil, null, nothing

    # Variable & Declaration Keywords
    SET = auto()
    LET = auto()
    TO = auto()
    CONSTANT = auto()
    DEFINE = auto()
    CREATE = auto()
    CALLED = auto()
    CHANGE = auto()
    INCREASE = auto()
    DECREASE = auto()
    BY = auto()

    # Functions & Types
    FUNCTION = auto()
    METHOD = auto()
    WITH = auto()
    RETURN = auto()
    ASYNC = auto()
    WAIT = auto()

    # Control Flow
    IF = auto()
    OTHERWISE = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    EACH = auto()
    IN = auto()
    REPEAT = auto()
    TIMES = auto()
    BREAK = auto()
    CONTINUE = auto()

    # Error Handling
    TRY = auto()
    CATCH = auto()
    ERROR = auto()
    AS = auto()
    FINALLY = auto()
    RAISE = auto()
    THROW = auto()

    # Modules
    IMPORT = auto()
    FROM = auto()

    # Network / HTTP / Backend Server
    SEND = auto()
    REQUEST = auto()
    SAVE = auto()
    RESPONSE = auto()
    HEADERS = auto()
    DATA = auto()
    PARAMS = auto()
    TIMEOUT = auto()

    SERVE = auto()
    PORT = auto()
    ROUTE = auto()
    USE = auto()
    MIDDLEWARE = auto()
    RESPOND = auto()
    STATUS = auto()
    VALIDATE = auto()
    BODY = auto()

    # I/O
    PRINT = auto()
    ASK = auto()
    ASSERT = auto()

    # Logical & English comparison keywords
    AND = auto()
    OR = auto()
    NOT = auto()
    IS = auto()
    EQUAL = auto()
    EQUALS = auto()
    GREATER = auto()
    LESS = auto()
    THAN = auto()
    AT = auto()
    LEAST = auto()
    MOST = auto()

    # Symbols & Operators
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    PERCENT = auto()        # %

    EQUAL_SIGN = auto()     # =
    EQUAL_EQUAL = auto()    # ==
    BANG_EQUAL = auto()     # !=
    GREATER_THAN = auto()   # >
    GREATER_EQUAL = auto()  # >=
    LESS_THAN = auto()      # <
    LESS_EQUAL = auto()     # <=

    COLON = auto()          # :
    COMMA = auto()          # ,
    DOT = auto()            # .
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    LBRACE = auto()         # {
    RBRACE = auto()         # }

    # Layout tokens
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


# Keyword lookup table (case-insensitive in lexer)
KEYWORDS: dict[str, TokenType] = {
    "set": TokenType.SET,
    "let": TokenType.LET,
    "to": TokenType.TO,
    "constant": TokenType.CONSTANT,
    "define": TokenType.DEFINE,
    "create": TokenType.CREATE,
    "called": TokenType.CALLED,
    "change": TokenType.CHANGE,
    "increase": TokenType.INCREASE,
    "decrease": TokenType.DECREASE,
    "by": TokenType.BY,

    "function": TokenType.FUNCTION,
    "method": TokenType.METHOD,
    "with": TokenType.WITH,
    "return": TokenType.RETURN,
    "nothing": TokenType.NIL,
    "async": TokenType.ASYNC,
    "wait": TokenType.WAIT,

    "if": TokenType.IF,
    "otherwise": TokenType.OTHERWISE,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "each": TokenType.EACH,
    "in": TokenType.IN,
    "repeat": TokenType.REPEAT,
    "times": TokenType.TIMES,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,

    "try": TokenType.TRY,
    "catch": TokenType.CATCH,
    "error": TokenType.ERROR,
    "as": TokenType.AS,
    "finally": TokenType.FINALLY,
    "raise": TokenType.RAISE,
    "throw": TokenType.THROW,

    "import": TokenType.IMPORT,
    "from": TokenType.FROM,

    "send": TokenType.SEND,
    "request": TokenType.REQUEST,
    "save": TokenType.SAVE,
    "response": TokenType.RESPONSE,
    "headers": TokenType.HEADERS,
    "data": TokenType.DATA,
    "params": TokenType.PARAMS,
    "timeout": TokenType.TIMEOUT,

    "serve": TokenType.SERVE,
    "port": TokenType.PORT,
    "route": TokenType.ROUTE,
    "use": TokenType.USE,
    "middleware": TokenType.MIDDLEWARE,
    "respond": TokenType.RESPOND,
    "status": TokenType.STATUS,
    "validate": TokenType.VALIDATE,
    "body": TokenType.BODY,

    "print": TokenType.PRINT,
    "ask": TokenType.ASK,
    "assert": TokenType.ASSERT,

    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "is": TokenType.IS,
    "equal": TokenType.EQUAL,
    "equals": TokenType.EQUALS,
    "greater": TokenType.GREATER,
    "less": TokenType.LESS,
    "than": TokenType.THAN,
    "at": TokenType.AT,
    "least": TokenType.LEAST,
    "most": TokenType.MOST,

    "true": TokenType.TRUE,
    "yes": TokenType.TRUE,
    "false": TokenType.FALSE,
    "no": TokenType.FALSE,
    "nil": TokenType.NIL,
    "null": TokenType.NIL,
}


@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int
    length: int = 1

    def __repr__(self) -> str:
        if self.literal is not None:
            return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r}, {self.line}:{self.column})"
        return f"Token({self.type.name}, {self.lexeme!r}, {self.line}:{self.column})"
