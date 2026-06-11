"""
Haiku Parser
============
Recursive-descent parser that transforms a token stream into an AST.
Implements precedence climbing for expressions and handles all Haiku
statements including functions, classes, control flow, and pattern matching.
"""

from typing import List, Optional
from lexer import Token, TokenType
from ast_nodes import (
    Program, Stmt, Expr, Param, VarDecl, FnDecl, ClassDecl,
    IfStmt, ForStmt, WhileStmt, MatchStmt, MatchCase, TryStmt,
    ThrowStmt, ReturnStmt, BreakStmt, ContinueStmt, Block, ExprStmt,
    ImportStmt, Literal, Identifier, BinaryExpr, UnaryExpr, AssignExpr,
    CallExpr, MemberExpr, IndexExpr, ListExpr, MapExpr, MapEntry,
    LambdaExpr, TernaryExpr, ThisExpr, SuperExpr
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        body: List[Stmt] = []
        while not self._at_end():
            self._skip_newlines()
            if self._at_end():
                break
            body.append(self._statement())
        return Program(body)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def _advance(self) -> Token:
        if not self._at_end():
            self.pos += 1
        return self._previous()

    def _check(self, *types: TokenType) -> bool:
        if self._at_end():
            return False
        return self._peek().type in types

    def _match(self, *types: TokenType) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _expect(self, ttype: TokenType, message: str) -> Token:
        if self._check(ttype):
            return self._advance()
        tok = self._peek()
        raise ParseError(f"{message} (got {tok.type.name} '{tok.value}' at line {tok.line})")

    def _skip_newlines(self):
        while self._check(TokenType.NEWLINE):
            self._advance()

    def _consume_statement_end(self):
        if self._check(TokenType.NEWLINE):
            self._advance()
        elif not self._check(TokenType.RBRACE, TokenType.EOF):
            if self._check(TokenType.SEMICOLON):
                self._advance()

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _statement(self) -> Stmt:
        self._skip_newlines()
        if self._check(TokenType.LET, TokenType.CONST):
            return self._var_decl()
        if self._check(TokenType.FN):
            return self._fn_decl(is_static=False)
        if self._check(TokenType.CLASS):
            return self._class_decl()
        if self._check(TokenType.IF):
            return self._if_stmt()
        if self._check(TokenType.FOR):
            return self._for_stmt()
        if self._check(TokenType.WHILE):
            return self._while_stmt()
        if self._check(TokenType.MATCH):
            return self._match_stmt()
        if self._check(TokenType.TRY):
            return self._try_stmt()
        if self._check(TokenType.THROW):
            return self._throw_stmt()
        if self._check(TokenType.RETURN):
            return self._return_stmt()
        if self._check(TokenType.BREAK):
            return self._break_stmt()
        if self._check(TokenType.CONTINUE):
            return self._continue_stmt()
        if self._check(TokenType.IMPORT):
            return self._import_stmt()
        if self._check(TokenType.STATIC):
            self._advance()
            if self._check(TokenType.FN):
                return self._fn_decl(is_static=True)
            raise ParseError("Expected 'fn' after 'static'")
        return self._expr_stmt()

    def _var_decl(self) -> VarDecl:
        kind = "let" if self._advance().type == TokenType.LET else "const"
        name = self._expect(TokenType.IDENTIFIER, "Expected variable name").value
        init = self._expression() if self._match(TokenType.ASSIGN) else None
        self._consume_statement_end()
        return VarDecl(kind, name, init)

    def _fn_decl(self, is_static: bool) -> FnDecl:
        self._expect(TokenType.FN, "Expected 'fn'")
        name = self._expect(TokenType.IDENTIFIER, "Expected function name").value
        self._expect(TokenType.LPAREN, "Expected '(' after function name")
        params = self._parameters()
        self._expect(TokenType.RPAREN, "Expected ')' after parameters")
        self._expect(TokenType.LBRACE, "Expected '{' before function body")
        body = self._block_body()
        return FnDecl(name, params, body, is_static)

    def _parameters(self) -> List[Param]:
        params: List[Param] = []
        if not self._check(TokenType.RPAREN):
            while True:
                pname = self._expect(TokenType.IDENTIFIER, "Expected parameter name").value
                default = self._expression() if self._match(TokenType.ASSIGN) else None
                params.append(Param(pname, default))
                if not self._match(TokenType.COMMA):
                    break
        return params

    def _class_decl(self) -> ClassDecl:
        self._expect(TokenType.CLASS, "Expected 'class'")
        name = self._expect(TokenType.IDENTIFIER, "Expected class name").value
        superclass = None
        if self._match(TokenType.LPAREN):
            superclass = Identifier(self._expect(TokenType.IDENTIFIER, "Expected superclass name").value)
            self._expect(TokenType.RPAREN, "Expected ')' after superclass")
        self._expect(TokenType.LBRACE, "Expected '{' before class body")
        methods: List[FnDecl] = []
        self._skip_newlines()
        while not self._check(TokenType.RBRACE) and not self._at_end():
            is_static = False
            if self._check(TokenType.STATIC):
                self._advance()
                is_static = True
            self._expect(TokenType.FN, "Expected method declaration")
            mname = self._expect(TokenType.IDENTIFIER, "Expected method name").value
            self._expect(TokenType.LPAREN, "Expected '(' after method name")
            params = self._parameters()
            self._expect(TokenType.RPAREN, "Expected ')' after parameters")
            self._expect(TokenType.LBRACE, "Expected '{' before method body")
            mbody = self._block_body()
            methods.append(FnDecl(mname, params, mbody, is_static))
            self._skip_newlines()
        self._expect(TokenType.RBRACE, "Expected '}' after class body")
        return ClassDecl(name, superclass, methods)

    def _if_stmt(self) -> IfStmt:
        self._expect(TokenType.IF, "Expected 'if'")
        return self._if_tail()

    def _if_tail(self) -> IfStmt:
        """Parse the condition, body, and any elif/else of an if statement."""
        condition = self._expression()
        self._expect(TokenType.LBRACE, "Expected '{' after if condition")
        consequent = Block(self._block_body())
        alternate = None
        self._skip_newlines()
        if self._match(TokenType.ELIF):
            alternate = self._if_tail()
        elif self._match(TokenType.ELSE):
            self._expect(TokenType.LBRACE, "Expected '{' after else")
            alternate = Block(self._block_body())
        return IfStmt(condition, consequent, alternate)

    def _for_stmt(self) -> ForStmt:
        self._expect(TokenType.FOR, "Expected 'for'")
        var = self._expect(TokenType.IDENTIFIER, "Expected loop variable").value
        self._expect(TokenType.IN, "Expected 'in' after loop variable")
        iterable = self._expression()
        self._expect(TokenType.LBRACE, "Expected '{' after for iterable")
        body = Block(self._block_body())
        return ForStmt(var, iterable, body)

    def _while_stmt(self) -> WhileStmt:
        self._expect(TokenType.WHILE, "Expected 'while'")
        condition = self._expression()
        self._expect(TokenType.LBRACE, "Expected '{' after while condition")
        body = Block(self._block_body())
        return WhileStmt(condition, body)

    def _match_stmt(self) -> MatchStmt:
        self._expect(TokenType.MATCH, "Expected 'match'")
        expr = self._expression()
        self._expect(TokenType.LBRACE, "Expected '{' after match expression")
        self._skip_newlines()
        cases: List[MatchCase] = []
        default = None
        while not self._check(TokenType.RBRACE) and not self._at_end():
            if self._check(TokenType.DEFAULT):
                self._advance()
                self._expect(TokenType.FAT_ARROW, "Expected '=>' after default")
                default = self._statement()
                self._skip_newlines()
            else:
                pattern = self._expression()
                self._expect(TokenType.FAT_ARROW, "Expected '=>' after pattern")
                body = self._statement()
                cases.append(MatchCase(pattern, body))
                self._skip_newlines()
        self._expect(TokenType.RBRACE, "Expected '}' after match cases")
        return MatchStmt(expr, cases, default)

    def _try_stmt(self) -> TryStmt:
        self._expect(TokenType.TRY, "Expected 'try'")
        self._expect(TokenType.LBRACE, "Expected '{' after try")
        body = self._block_body()
        catch_param = None
        catch_body = None
        finally_body = None
        self._skip_newlines()
        if self._match(TokenType.CATCH):
            if self._check(TokenType.IDENTIFIER):
                catch_param = self._advance().value
            self._expect(TokenType.LBRACE, "Expected '{' after catch")
            catch_body = self._block_body()
        self._skip_newlines()
        if self._match(TokenType.FINALLY):
            self._expect(TokenType.LBRACE, "Expected '{' after finally")
            finally_body = self._block_body()
        return TryStmt(body, catch_param, catch_body, finally_body)

    def _throw_stmt(self) -> ThrowStmt:
        self._expect(TokenType.THROW, "Expected 'throw'")
        expr = self._expression()
        self._consume_statement_end()
        return ThrowStmt(expr)

    def _return_stmt(self) -> ReturnStmt:
        self._expect(TokenType.RETURN, "Expected 'return'")
        expr = None
        if not self._check(TokenType.NEWLINE, TokenType.RBRACE, TokenType.EOF):
            expr = self._expression()
        self._consume_statement_end()
        return ReturnStmt(expr)

    def _break_stmt(self) -> BreakStmt:
        self._expect(TokenType.BREAK, "Expected 'break'")
        self._consume_statement_end()
        return BreakStmt()

    def _continue_stmt(self) -> ContinueStmt:
        self._expect(TokenType.CONTINUE, "Expected 'continue'")
        self._consume_statement_end()
        return ContinueStmt()

    def _import_stmt(self) -> ImportStmt:
        self._expect(TokenType.IMPORT, "Expected 'import'")
        names: List[str] = []
        if self._match(TokenType.LBRACE):
            while True:
                names.append(self._expect(TokenType.IDENTIFIER, "Expected import name").value)
                if not self._match(TokenType.COMMA):
                    break
            self._expect(TokenType.RBRACE, "Expected '}' after imports")
        else:
            names.append(self._expect(TokenType.IDENTIFIER, "Expected import name").value)
        alias = self._expect(TokenType.IDENTIFIER, "Expected alias name").value if self._match(TokenType.AS) else None
        path = self._expect(TokenType.STRING, "Expected module path").value if self._match(TokenType.FROM) else None
        self._consume_statement_end()
        return ImportStmt(names, alias, path)

    def _block_body(self) -> List[Stmt]:
        body: List[Stmt] = []
        self._skip_newlines()
        while not self._check(TokenType.RBRACE) and not self._at_end():
            body.append(self._statement())
            self._skip_newlines()
        self._expect(TokenType.RBRACE, "Expected '}'")
        return body

    def _expr_stmt(self) -> ExprStmt:
        expr = self._expression()
        self._consume_statement_end()
        return ExprStmt(expr)

    # ------------------------------------------------------------------
    # Expressions (precedence climbing)
    # ------------------------------------------------------------------

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expr = self._ternary()
        if self._match(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                       TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN):
            op = self._previous().value
            value = self._assignment()
            if isinstance(expr, (Identifier, MemberExpr, IndexExpr)):
                return AssignExpr(expr, op, value)
            raise ParseError("Invalid assignment target")
        return expr

    def _ternary(self) -> Expr:
        expr = self._or()
        if self._match(TokenType.QUESTION):
            consequent = self._expression()
            self._expect(TokenType.COLON, "Expected ':' in ternary")
            alternate = self._ternary()
            return TernaryExpr(expr, consequent, alternate)
        return expr

    def _or(self) -> Expr:
        expr = self._and()
        while self._match(TokenType.OR_OR):
            expr = BinaryExpr(expr, self._previous().value, self._and())
        return expr

    def _and(self) -> Expr:
        expr = self._equality()
        while self._match(TokenType.AND_AND):
            expr = BinaryExpr(expr, self._previous().value, self._equality())
        return expr

    def _equality(self) -> Expr:
        expr = self._comparison()
        while self._match(TokenType.EQ, TokenType.NEQ):
            expr = BinaryExpr(expr, self._previous().value, self._comparison())
        return expr

    def _comparison(self) -> Expr:
        expr = self._range()
        while self._match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            expr = BinaryExpr(expr, self._previous().value, self._range())
        return expr

    def _range(self) -> Expr:
        expr = self._bitwise()
        if self._match(TokenType.DOT_DOT):
            return BinaryExpr(expr, "..", self._bitwise())
        return expr

    def _bitwise(self) -> Expr:
        expr = self._shift()
        while self._match(TokenType.BOR, TokenType.BXOR, TokenType.BAND):
            expr = BinaryExpr(expr, self._previous().value, self._shift())
        return expr

    def _shift(self) -> Expr:
        expr = self._additive()
        while self._match(TokenType.LSHIFT, TokenType.RSHIFT):
            expr = BinaryExpr(expr, self._previous().value, self._additive())
        return expr

    def _additive(self) -> Expr:
        expr = self._multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            expr = BinaryExpr(expr, self._previous().value, self._multiplicative())
        return expr

    def _multiplicative(self) -> Expr:
        expr = self._power()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            expr = BinaryExpr(expr, self._previous().value, self._power())
        return expr

    def _power(self) -> Expr:
        expr = self._unary()
        if self._match(TokenType.POWER):
            return BinaryExpr(expr, "**", self._power())  # right-assoc
        return expr

    def _unary(self) -> Expr:
        if self._match(TokenType.BANG, TokenType.MINUS, TokenType.BNOT, TokenType.NOT):
            return UnaryExpr(self._previous().value, self._unary())
        return self._postfix()

    def _postfix(self) -> Expr:
        expr = self._primary()
        while True:
            if self._match(TokenType.LPAREN):
                args = self._arguments()
                self._expect(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExpr(expr, args)
            elif self._match(TokenType.LBRACKET):
                idx = self._expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexExpr(expr, idx)
            elif self._match(TokenType.DOT):
                prop = self._expect(TokenType.IDENTIFIER, "Expected property name after '.'").value
                expr = MemberExpr(expr, prop, False)
            elif self._match(TokenType.QDOT):
                prop = self._expect(TokenType.IDENTIFIER, "Expected property after '?.'").value
                expr = MemberExpr(expr, prop, True)
            else:
                break
        return expr

    def _primary(self) -> Expr:
        if self._match(TokenType.TRUE):
            return Literal(True)
        if self._match(TokenType.FALSE):
            return Literal(False)
        if self._match(TokenType.NONE):
            return Literal(None)
        if self._match(TokenType.NUMBER):
            return Literal(float(self._previous().value))
        if self._match(TokenType.STRING):
            return Literal(self._previous().value)
        if self._match(TokenType.IDENTIFIER):
            return Identifier(self._previous().value)
        if self._match(TokenType.THIS):
            return ThisExpr()
        if self._match(TokenType.SUPER):
            self._expect(TokenType.DOT, "Expected '.' after 'super'")
            method = self._expect(TokenType.IDENTIFIER, "Expected method name after 'super.'").value
            return SuperExpr(method)
        if self._match(TokenType.LPAREN):
            # Lambda detection
            saved = self.pos
            try:
                params = self._parameters()
                self._expect(TokenType.RPAREN, "Expected ')'")
                if self._match(TokenType.FAT_ARROW):
                    if self._check(TokenType.LBRACE):
                        self._advance()
                        body = self._block_body()
                        return LambdaExpr(params, body)
                    else:
                        body = self._expression()
                        return LambdaExpr(params, body)
            except ParseError:
                pass
            self.pos = saved
            expr = self._expression()
            self._expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        if self._match(TokenType.LBRACKET):
            elements: List[Expr] = []
            if not self._check(TokenType.RBRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._expect(TokenType.RBRACKET, "Expected ']' after list elements")
            return ListExpr(elements)
        if self._match(TokenType.LBRACE):
            entries: List[MapEntry] = []
            if not self._check(TokenType.RBRACE):
                while True:
                    key = self._expression()
                    self._expect(TokenType.COLON, "Expected ':' in map entry")
                    value = self._expression()
                    entries.append(MapEntry(key, value))
                    if not self._match(TokenType.COMMA):
                        break
            self._expect(TokenType.RBRACE, "Expected '}' after map entries")
            return MapExpr(entries)
        if self._match(TokenType.FN):
            self._expect(TokenType.LPAREN, "Expected '('")
            params = self._parameters()
            self._expect(TokenType.RPAREN, "Expected ')'")
            self._expect(TokenType.LBRACE, "Expected '{'")
            body = self._block_body()
            return LambdaExpr(params, body)

        tok = self._peek()
        raise ParseError(f"Unexpected token {tok.type.name} '{tok.value}' at line {tok.line}")

    def _arguments(self) -> List[Expr]:
        args: List[Expr] = []
        if not self._check(TokenType.RPAREN):
            while True:
                args.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        return args
