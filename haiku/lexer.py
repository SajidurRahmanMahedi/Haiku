"""
Haiku Lexer (Tokenizer)
=======================
Converts raw Haiku source code into a stream of tokens.
Handles keywords, identifiers, literals, comments, operators,
and all escape sequences.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    FSTRING = auto()
    RSTRING = auto()
    IDENTIFIER = auto()

    # Keywords
    LET = auto(); CONST = auto(); FN = auto()
    IF = auto(); ELSE = auto(); ELIF = auto()
    FOR = auto(); WHILE = auto(); RETURN = auto()
    CLASS = auto(); THIS = auto(); SUPER = auto()
    IMPORT = auto(); FROM = auto(); AS = auto()
    TRUE = auto(); FALSE = auto(); NONE = auto()
    AND = auto(); OR = auto(); NOT = auto()
    TRY = auto(); CATCH = auto(); FINALLY = auto()
    THROW = auto(); MATCH = auto(); CASE = auto()
    DEFAULT = auto(); BREAK = auto(); CONTINUE = auto()
    IN = auto(); ASYNC = auto(); AWAIT = auto()
    YIELD = auto(); STATIC = auto()
    PRIVATE = auto(); PUBLIC = auto()

    # Operators
    PLUS = auto(); MINUS = auto(); STAR = auto()
    SLASH = auto(); PERCENT = auto(); POWER = auto()
    EQ = auto(); NEQ = auto(); LT = auto(); GT = auto()
    LTE = auto(); GTE = auto(); ASSIGN = auto()
    PLUS_ASSIGN = auto(); MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto(); SLASH_ASSIGN = auto()
    AND_AND = auto(); OR_OR = auto(); BANG = auto()
    BAND = auto(); BOR = auto(); BXOR = auto()
    BNOT = auto(); LSHIFT = auto(); RSHIFT = auto()
    QUESTION = auto(); COLON = auto()
    ARROW = auto(); FAT_ARROW = auto()
    DOT = auto(); DOT_DOT = auto(); QDOT = auto()

    # Delimiters
    LPAREN = auto(); RPAREN = auto()
    LBRACE = auto(); RBRACE = auto()
    LBRACKET = auto(); RBRACKET = auto()
    COMMA = auto(); SEMICOLON = auto()
    NEWLINE = auto()

    EOF = auto()


KEYWORDS = {
    "let": TokenType.LET, "const": TokenType.CONST,
    "fn": TokenType.FN, "if": TokenType.IF,
    "else": TokenType.ELSE, "elif": TokenType.ELIF,
    "for": TokenType.FOR, "while": TokenType.WHILE,
    "return": TokenType.RETURN, "class": TokenType.CLASS,
    "this": TokenType.THIS, "super": TokenType.SUPER,
    "import": TokenType.IMPORT, "from": TokenType.FROM,
    "as": TokenType.AS, "true": TokenType.TRUE,
    "false": TokenType.FALSE, "none": TokenType.NONE,
    "and": TokenType.AND, "or": TokenType.OR,
    "not": TokenType.NOT, "try": TokenType.TRY,
    "catch": TokenType.CATCH, "finally": TokenType.FINALLY,
    "throw": TokenType.THROW, "match": TokenType.MATCH,
    "case": TokenType.CASE, "default": TokenType.DEFAULT,
    "break": TokenType.BREAK, "continue": TokenType.CONTINUE,
    "in": TokenType.IN, "async": TokenType.ASYNC,
    "await": TokenType.AWAIT, "yield": TokenType.YIELD,
    "static": TokenType.STATIC, "private": TokenType.PRIVATE,
    "public": TokenType.PUBLIC,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int


class LexerError(Exception):
    pass


class Lexer:
    """Tokenizes Haiku source code."""

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.bracket_depth = 0

    def tokenize(self) -> List[Token]:
        while not self._at_end():
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _peek(self) -> str:
        return "\0" if self._at_end() else self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    def _add_token(self, ttype: TokenType, value: str):
        self.tokens.append(Token(ttype, value, self.line, self.column - len(value)))

    # ------------------------------------------------------------------
    # Main scanner
    # ------------------------------------------------------------------

    def _scan_token(self):
        ch = self._advance()

        # Single-character tokens & brackets
        if ch == "(":
            self.bracket_depth += 1; self._add_token(TokenType.LPAREN, ch)
        elif ch == ")":
            self.bracket_depth -= 1; self._add_token(TokenType.RPAREN, ch)
        elif ch == "{":
            self.bracket_depth += 1; self._add_token(TokenType.LBRACE, ch)
        elif ch == "}":
            self.bracket_depth -= 1; self._add_token(TokenType.RBRACE, ch)
        elif ch == "[":
            self.bracket_depth += 1; self._add_token(TokenType.LBRACKET, ch)
        elif ch == "]":
            self.bracket_depth -= 1; self._add_token(TokenType.RBRACKET, ch)
        elif ch == ",":
            self._add_token(TokenType.COMMA, ch)
        elif ch == ";":
            self._add_token(TokenType.SEMICOLON, ch)

        # Operators
        elif ch == "+":
            if self._match("="):
                self._add_token(TokenType.PLUS_ASSIGN, "+=")
            else:
                self._add_token(TokenType.PLUS, "+")
        elif ch == "-":
            if self._match("="):
                self._add_token(TokenType.MINUS_ASSIGN, "-=")
            elif self._match(">"):
                self._add_token(TokenType.ARROW, "->")
            else:
                self._add_token(TokenType.MINUS, "-")
        elif ch == "*":
            if self._match("*"):
                self._add_token(TokenType.POWER, "**")
            elif self._match("="):
                self._add_token(TokenType.STAR_ASSIGN, "*=")
            else:
                self._add_token(TokenType.STAR, "*")
        elif ch == "/":
            if self._match("/"):
                while self._peek() != "\n" and not self._at_end():
                    self._advance()
            elif self._match("*"):
                self._block_comment()
            elif self._match("="):
                self._add_token(TokenType.SLASH_ASSIGN, "/=")
            else:
                self._add_token(TokenType.SLASH, "/")
        elif ch == "%":
            self._add_token(TokenType.PERCENT, "%")
        elif ch == "=":
            if self._match("="):
                self._add_token(TokenType.EQ, "==")
            elif self._match(">"):
                self._add_token(TokenType.FAT_ARROW, "=>")
            else:
                self._add_token(TokenType.ASSIGN, "=")
        elif ch == "!":
            if self._match("="):
                self._add_token(TokenType.NEQ, "!=")
            else:
                self._add_token(TokenType.BANG, "!")
        elif ch == "<":
            if self._match("="):
                self._add_token(TokenType.LTE, "<=")
            elif self._match("<"):
                self._add_token(TokenType.LSHIFT, "<<")
            else:
                self._add_token(TokenType.LT, "<")
        elif ch == ">":
            if self._match("="):
                self._add_token(TokenType.GTE, ">=")
            elif self._match(">"):
                self._add_token(TokenType.RSHIFT, ">>")
            else:
                self._add_token(TokenType.GT, ">")
        elif ch == "&":
            if self._match("&"):
                self._add_token(TokenType.AND_AND, "&&")
            else:
                self._add_token(TokenType.BAND, "&")
        elif ch == "|":
            if self._match("|"):
                self._add_token(TokenType.OR_OR, "||")
            else:
                self._add_token(TokenType.BOR, "|")
        elif ch == "^":
            self._add_token(TokenType.BXOR, "^")
        elif ch == "~":
            self._add_token(TokenType.BNOT, "~")
        elif ch == "?":
            if self._match("."):
                self._add_token(TokenType.QDOT, "?.")
            else:
                self._add_token(TokenType.QUESTION, "?")
        elif ch == ":":
            self._add_token(TokenType.COLON, ":")
        elif ch == ".":
            if self._match("."):
                self._add_token(TokenType.DOT_DOT, "..")
            else:
                self._add_token(TokenType.DOT, ".")

        # Literals
        elif ch == '"':
            self._string('"')
        elif ch == "'":
            self._string("'")

        # Whitespace
        elif ch == "\n":
            if self.bracket_depth == 0:
                self._add_token(TokenType.NEWLINE, "\n")
        elif ch in " \r\t":
            pass

        # Numbers & identifiers
        elif self._is_digit(ch):
            self._number(ch)
        elif self._is_alpha(ch):
            # Check for string prefix (f or r followed by quote)
            if ch in ('f', 'r') and self._peek() in ('"', "'"):
                quote = self._advance()
                if ch == 'f':
                    self._fstring(quote)
                else:
                    self._rstring(quote)
            else:
                self._identifier(ch)
        else:
            raise LexerError(f"Unexpected character '{ch}' at line {self.line}, column {self.column}")

    # ------------------------------------------------------------------
    # Detailed scanners
    # ------------------------------------------------------------------

    def _block_comment(self):
        start_line = self.line
        while not (self._peek() == "*" and self._peek_next() == "/") and not self._at_end():
            self._advance()
        if self._at_end():
            raise LexerError(
                f"Unterminated block comment starting at line {start_line}"
            )
        self._advance()  # *
        self._advance()  # /


    def _string(self, quote: str):
        value = ""
        while self._peek() != quote and not self._at_end():
            if self._peek() == "\\":
                self._advance()
                esc = self._advance()
                value += {"n": "\n", "t": "\t", "r": "\r", "\\": "\\",
                          '"': '"', "'": "'", "0": "\0"}.get(esc, esc)
            else:
                value += self._advance()
        if self._at_end():
            raise LexerError(f"Unterminated string at line {self.line}")
        self._advance()  # closing quote
        self._add_token(TokenType.STRING, value)

    def _rstring(self, quote: str):
        """Raw string - no escape sequences."""
        value = ""
        while self._peek() != quote and not self._at_end():
            value += self._advance()
        if self._at_end():
            raise LexerError(f"Unterminated raw string at line {self.line}")
        self._advance()  # closing quote
        self._add_token(TokenType.RSTRING, value)

    def _fstring(self, quote: str):
        """F-string with interpolation."""
        value = ""
        while self._peek() != quote and not self._at_end():
            if self._peek() == "\\":
                self._advance()
                esc = self._advance()
                value += {"n": "\n", "t": "\t", "r": "\r", "\\": "\\",
                          '"': '"', "'": "'", "0": "\0"}.get(esc, esc)
            elif self._peek() == "{" and self._peek_next() == "{":
                # Escaped brace {{
                self._advance()
                self._advance()
                value += "{"
            elif self._peek() == "}" and self._peek_next() == "}":
                # Escaped brace }}
                self._advance()
                self._advance()
                value += "}"
            elif self._peek() == "{":
                # Start of interpolation
                self._advance()
                value += "{"  # Mark interpolation start
            elif self._peek() == "}":
                # End of interpolation
                self._advance()
                value += "}"  # Mark interpolation end
            else:
                value += self._advance()
        if self._at_end():
            raise LexerError(f"Unterminated f-string at line {self.line}")
        self._advance()  # closing quote
        self._add_token(TokenType.FSTRING, value)

    def _number(self, first: str):
        value = first
        while self._is_digit(self._peek()):
            value += self._advance()
        if self._peek() == "." and self._is_digit(self._peek_next()):
            value += self._advance()
            while self._is_digit(self._peek()):
                value += self._advance()
        self._add_token(TokenType.NUMBER, value)

    def _identifier(self, first: str):
        value = first
        while self._is_alpha_numeric(self._peek()):
            value += self._advance()
        ttype = KEYWORDS.get(value, TokenType.IDENTIFIER)
        self._add_token(ttype, value)

    @staticmethod
    def _is_digit(ch: str) -> bool:
        return "0" <= ch <= "9"

    @staticmethod
    def _is_alpha(ch: str) -> bool:
        return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"

    def _is_alpha_numeric(self, ch: str) -> bool:
        return self._is_alpha(ch) or self._is_digit(ch)
