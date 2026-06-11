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


@dataclass
class Identifier:
    """Variable or function name."""
    name: str


@dataclass
class BinaryExpr:
    """Binary operation: left op right"""
    left: "Expr"
    operator: str
    right: "Expr"


@dataclass
class UnaryExpr:
    """Unary operation: op operand"""
    operator: str
    operand: "Expr"


@dataclass
class AssignExpr:
    """Assignment: target = value (or +=, -=, etc.)"""
    target: "Expr"
    operator: str
    value: "Expr"


@dataclass
class CallExpr:
    """Function or method call."""
    callee: "Expr"
    args: List["Expr"]


@dataclass
class MemberExpr:
    """Property access: obj.property or obj?.property"""
    obj: "Expr"
    property: str
    optional: bool = False


@dataclass
class IndexExpr:
    """Index access: obj[index]"""
    obj: "Expr"
    index: "Expr"


@dataclass
class ListExpr:
    """List literal: [1, 2, 3]"""
    elements: List["Expr"]


@dataclass
class MapEntry:
    """Single key:value pair inside a map literal."""
    key: "Expr"
    value: "Expr"


@dataclass
class MapExpr:
    """Map literal: {"a": 1, "b": 2}"""
    entries: List[MapEntry]


@dataclass
class LambdaExpr:
    """Anonymous function / lambda: (x) => x * 2  or fn(x) { ... }"""
    params: List["Param"]
    body: Union["Expr", List["Stmt"]]


@dataclass
class TernaryExpr:
    """Ternary: condition ? consequent : alternate"""
    condition: "Expr"
    consequent: "Expr"
    alternate: "Expr"


@dataclass
class ThisExpr:
    """Reference to current object instance."""
    pass


@dataclass
class SuperExpr:
    """Reference to superclass method: super.method()"""
    method: str


Expr = Union[
    Literal, Identifier, BinaryExpr, UnaryExpr, AssignExpr,
    CallExpr, MemberExpr, IndexExpr, ListExpr, MapExpr,
    LambdaExpr, TernaryExpr, ThisExpr, SuperExpr
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


@dataclass
class FnDecl:
    """Function declaration: fn name(params) { body }"""
    name: str
    params: List[Param]
    body: List["Stmt"]
    is_static: bool = False


@dataclass
class ClassDecl:
    """Class declaration: class Name(Super) { methods... }"""
    name: str
    superclass: Optional[Identifier]
    methods: List[FnDecl]


@dataclass
class IfStmt:
    """If statement with optional elif/else chains."""
    condition: Expr
    consequent: "Stmt"
    alternate: Optional["Stmt"] = None


@dataclass
class ForStmt:
    """For-in loop: for x in iterable { body }"""
    variable: str
    iterable: Expr
    body: "Stmt"


@dataclass
class WhileStmt:
    """While loop: while condition { body }"""
    condition: Expr
    body: "Stmt"


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


@dataclass
class TryStmt:
    """Exception handling: try { } catch e { } finally { }"""
    body: List["Stmt"]
    catch_param: Optional[str] = None
    catch_body: Optional[List["Stmt"]] = None
    finally_body: Optional[List["Stmt"]] = None


@dataclass
class ThrowStmt:
    """Throw an exception."""
    expr: Expr


@dataclass
class ReturnStmt:
    """Return from a function."""
    expr: Optional[Expr] = None


@dataclass
class BreakStmt:
    """Break out of a loop."""
    pass


@dataclass
class ContinueStmt:
    """Skip to next loop iteration."""
    pass


@dataclass
class Block:
    """Block of statements: { stmt; stmt; }"""
    body: List["Stmt"]


@dataclass
class ExprStmt:
    """Expression used as a statement."""
    expr: Expr


@dataclass
class ImportStmt:
    """Import statement: import { a, b } from 'module'"""
    names: List[str]
    alias: Optional[str] = None
    path: Optional[str] = None


Stmt = Union[
    VarDecl, FnDecl, ClassDecl, IfStmt, ForStmt, WhileStmt,
    MatchStmt, TryStmt, ThrowStmt, ReturnStmt, BreakStmt,
    ContinueStmt, Block, ExprStmt, ImportStmt
]


@dataclass
class Program:
    """Root node of every Haiku program."""
    body: List[Stmt]
