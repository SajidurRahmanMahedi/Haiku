"""
Haiku Abstract Syntax Tree (AST) Node Definitions
=================================================
Every construct in the Haiku language is represented as a node in the AST.
The parser transforms token streams into these nodes, and the interpreter
walks the AST to execute the program.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass
class Literal:
    """Numeric, string, boolean, or none literal."""
    value: Union[int, float, str, bool, None]
    line: int = 0


@dataclass
class Identifier:
    """Variable or function name."""
    name: str
    line: int = 0


@dataclass
class BinaryExpr:
    """Binary operation: left op right"""
    left: "Expr"
    operator: str
    right: "Expr"
    line: int = 0


@dataclass
class UnaryExpr:
    """Unary operation: op operand"""
    operator: str
    operand: "Expr"
    line: int = 0


@dataclass
class AssignExpr:
    """Assignment: target = value (or +=, -=, etc.)"""
    target: "Expr"
    operator: str
    value: "Expr"
    line: int = 0


@dataclass
class CallExpr:
    """Function or method call."""
    callee: "Expr"
    args: List["Expr"]
    line: int = 0


@dataclass
class MemberExpr:
    """Property access: obj.property or obj?.property"""
    obj: "Expr"
    property: str
    optional: bool = False
    line: int = 0


@dataclass
class IndexExpr:
    """Index access: obj[index]"""
    obj: "Expr"
    index: "Expr"
    line: int = 0


@dataclass
class ListExpr:
    """List literal: [1, 2, 3]"""
    elements: List["Expr"]
    line: int = 0


@dataclass
class MapEntry:
    """Single key:value pair inside a map literal."""
    key: "Expr"
    value: "Expr"


@dataclass
class MapExpr:
    """Map literal: {"a": 1, "b": 2}"""
    entries: List[MapEntry]
    line: int = 0


@dataclass
class LambdaExpr:
    """Anonymous function / lambda: (x) => x * 2  or fn(x) { ... }"""
    params: List["Param"]
    body: Union["Expr", List["Stmt"]]
    line: int = 0


@dataclass
class TernaryExpr:
    """Ternary: condition ? consequent : alternate"""
    condition: "Expr"
    consequent: "Expr"
    alternate: "Expr"
    line: int = 0


@dataclass
class ThisExpr:
    """Reference to current object instance."""
    line: int = 0


@dataclass
class SuperExpr:
    """Reference to superclass method: super.method()"""
    method: str
    line: int = 0


@dataclass
class FString:
    """F-string with interpolation: f'Hello {name}'"""
    parts: List[Union[str, "Expr"]]  # Alternating string literals and expressions
    line: int = 0


Expr = Union[
    Literal, Identifier, BinaryExpr, UnaryExpr, AssignExpr,
    CallExpr, MemberExpr, IndexExpr, ListExpr, MapExpr,
    LambdaExpr, TernaryExpr, ThisExpr, SuperExpr, FString
]


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

@dataclass
class Param:
    """Function parameter with optional default value."""
    name: str
    default: Optional[Expr] = None


@dataclass
class VarDecl:
    """Variable declaration: let x = 10  or  const PI = 3.14"""
    kind: str          # "let" or "const"
    name: str
    init: Optional[Expr]
    line: int = 0


@dataclass
class FnDecl:
    """Function declaration: fn name(params) { body }"""
    name: str
    params: List[Param]
    body: List["Stmt"]
    is_static: bool = False
    line: int = 0


@dataclass
class ClassDecl:
    """Class declaration: class Name(Super) { methods... }"""
    name: str
    superclass: Optional[Identifier]
    methods: List[FnDecl]
    line: int = 0


@dataclass
class IfStmt:
    """If statement with optional elif/else chains."""
    condition: Expr
    consequent: "Stmt"
    alternate: Optional["Stmt"] = None
    line: int = 0


@dataclass
class ForStmt:
    """For-in loop: for x in iterable { body }"""
    variable: str
    iterable: Expr
    body: "Stmt"
    line: int = 0


@dataclass
class WhileStmt:
    """While loop: while condition { body }"""
    condition: Expr
    body: "Stmt"
    line: int = 0


@dataclass
class MatchCase:
    """Single case inside a match statement."""
    pattern: Expr
    body: "Stmt"


@dataclass
class MatchStmt:
    """Pattern matching: match expr { case => body ... }"""
    expr: Expr
    cases: List[MatchCase]
    default: Optional["Stmt"] = None
    line: int = 0


@dataclass
class TryStmt:
    """Exception handling: try { } catch e { } finally { }"""
    body: List["Stmt"]
    catch_param: Optional[str] = None
    catch_body: Optional[List["Stmt"]] = None
    finally_body: Optional[List["Stmt"]] = None
    line: int = 0


@dataclass
class ThrowStmt:
    """Throw an exception."""
    expr: Expr
    line: int = 0


@dataclass
class ReturnStmt:
    """Return from a function."""
    expr: Optional[Expr] = None
    line: int = 0


@dataclass
class BreakStmt:
    """Break out of a loop."""
    line: int = 0


@dataclass
class ContinueStmt:
    """Skip to next loop iteration."""
    line: int = 0


@dataclass
class Block:
    """Block of statements: { stmt; stmt; }"""
    body: List["Stmt"]
    line: int = 0


@dataclass
class ExprStmt:
    """Expression used as a statement."""
    expr: Expr
    line: int = 0


@dataclass
class ImportStmt:
    """Import statement: import { a, b } from 'module'"""
    names: List[str]
    alias: Optional[str] = None
    path: Optional[str] = None
    line: int = 0


Stmt = Union[
    VarDecl, FnDecl, ClassDecl, IfStmt, ForStmt, WhileStmt,
    MatchStmt, TryStmt, ThrowStmt, ReturnStmt, BreakStmt,
    ContinueStmt, Block, ExprStmt, ImportStmt
]


@dataclass
class Program:
    """Root node of every Haiku program."""
    body: List[Stmt]
