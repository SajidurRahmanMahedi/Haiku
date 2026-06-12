"""
Haiku Interpreter
=================
Tree-walking interpreter that executes the AST produced by the parser.
Supports functions, closures, classes, inheritance, exceptions, and
all built-in operations.

Error reporting includes line numbers and a call-stack traceback.
"""

from typing import List, Optional, Dict, Any
from .ast_nodes import (
    Program, Stmt, Expr, VarDecl, FnDecl, ClassDecl, IfStmt, ForStmt,
    WhileStmt, MatchStmt, TryStmt, ThrowStmt, ReturnStmt, BreakStmt,
    ContinueStmt, Block, ExprStmt, ImportStmt, Literal, Identifier,
    BinaryExpr, UnaryExpr, AssignExpr, CallExpr, MemberExpr, IndexExpr,
    ListExpr, MapExpr, MapEntry, LambdaExpr, TernaryExpr, ThisExpr, SuperExpr, FString
)
from .values import (
    HValue, HNumber, HString, HBoolean, HNone, HList, HMap,
    HFunction, HClass, HInstance, HNativeFn, HModule,
    Environment, is_truthy, h_number, h_string, h_bool, h_none, h_list, h_map
)


# ---------------------------------------------------------------------------
# Internal control-flow signals (not user-visible errors)
# ---------------------------------------------------------------------------

class ReturnException(Exception):
    def __init__(self, value: HValue):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


# ---------------------------------------------------------------------------
# Runtime error with traceback support
# ---------------------------------------------------------------------------

class HaikuRuntimeError(Exception):
    """
    A runtime error produced by the Haiku interpreter.
    Carries a message, the source line where it occurred, and a call-stack
    that is built up as the exception propagates through _call_function.
    """

    def __init__(self, message: str, line: int = 0):
        super().__init__(message)
        self.message = message
        self.line = line
        # Each frame: (fn_name, line)
        self.call_stack: List[tuple] = []

    def push_frame(self, fn_name: str, line: int):
        self.call_stack.append((fn_name, line))

    def format(self) -> str:
        """Produce a human-readable error with traceback."""
        lines = ["Traceback (most recent call last):"]
        # call_stack is innermost-first; reverse for Python-style display
        for fn_name, ln in reversed(self.call_stack):
            if ln:
                lines.append(f"  at line {ln} in {fn_name}")
            else:
                lines.append(f"  in {fn_name}")
        if self.line:
            lines.append(f"RuntimeError at line {self.line}: {self.message}")
        else:
            lines.append(f"RuntimeError: {self.message}")
        return "\n".join(lines)


# Keep old name as alias so existing code that catches RuntimeError still works
RuntimeError = HaikuRuntimeError


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------

class Interpreter:
    """Executes Haiku AST nodes."""

    def __init__(self, globals: Optional[Environment] = None):
        self.globals = globals or Environment()
        self.environment = self.globals
        self.output_buffer: List[str] = []
        self.input_provider: Optional[callable] = None
        # Current execution context label (for top-level frames)
        self._current_fn: str = "<module>"

    def set_input_provider(self, provider: callable):
        self.input_provider = provider

    def get_output(self) -> str:
        return "".join(self.output_buffer)

    def clear_output(self):
        self.output_buffer = []

    def write(self, text: str):
        self.output_buffer.append(text)

    def writeln(self, text: str):
        self.output_buffer.append(text + "\n")

    def read_input(self) -> str:
        if self.input_provider:
            return self.input_provider() or ""
        return ""

    def interpret(self, program: Program) -> HValue:
        result: HValue = h_none()
        for stmt in program.body:
            result = self._eval_stmt(stmt)
        return result

    # ------------------------------------------------------------------
    # Helper: get line from a node (0 if not available)
    # ------------------------------------------------------------------

    @staticmethod
    def _node_line(node) -> int:
        return getattr(node, "line", 0)

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _eval_stmt(self, stmt: Stmt) -> HValue:
        if isinstance(stmt, VarDecl):
            value = self._eval_expr(stmt.init) if stmt.init else h_none()
            self.environment.define(stmt.name, value)
            return value

        if isinstance(stmt, FnDecl):
            fn = HFunction(stmt.name, stmt.params, stmt.body, self.environment)
            fn.line = stmt.line
            self.environment.define(stmt.name, fn)
            return fn

        if isinstance(stmt, ClassDecl):
            superclass = None
            if stmt.superclass:
                sup = self.environment.get(stmt.superclass.name)
                if not isinstance(sup, HClass):
                    raise HaikuRuntimeError(
                        f"Superclass {stmt.superclass.name} is not a class",
                        stmt.line
                    )
                superclass = sup

            methods: Dict[str, HFunction] = {}
            static_methods: Dict[str, HFunction] = {}
            for method in stmt.methods:
                fn = HFunction(method.name, method.params, method.body, self.environment)
                fn.line = method.line
                if method.is_static:
                    static_methods[method.name] = fn
                else:
                    methods[method.name] = fn

            klass = HClass(stmt.name, superclass, methods, static_methods)
            self.environment.define(stmt.name, klass)
            return klass

        if isinstance(stmt, IfStmt):
            if is_truthy(self._eval_expr(stmt.condition)):
                return self._eval_stmt(stmt.consequent)
            elif stmt.alternate:
                return self._eval_stmt(stmt.alternate)
            return h_none()

        if isinstance(stmt, ForStmt):
            return self._eval_for(stmt)

        if isinstance(stmt, WhileStmt):
            return self._eval_while(stmt)

        if isinstance(stmt, MatchStmt):
            value = self._eval_expr(stmt.expr)
            for case in stmt.cases:
                pattern = self._eval_expr(case.pattern)
                if self._values_equal(value, pattern):
                    return self._eval_stmt(case.body)
            if stmt.default:
                return self._eval_stmt(stmt.default)
            return h_none()

        if isinstance(stmt, TryStmt):
            return self._eval_try(stmt)

        if isinstance(stmt, ThrowStmt):
            value = self._eval_expr(stmt.expr)
            raise HaikuRuntimeError(str(value), stmt.line)

        if isinstance(stmt, ReturnStmt):
            value = self._eval_expr(stmt.expr) if stmt.expr else h_none()
            raise ReturnException(value)

        if isinstance(stmt, BreakStmt):
            raise BreakException()

        if isinstance(stmt, ContinueStmt):
            raise ContinueException()

        if isinstance(stmt, Block):
            return self._eval_block(stmt.body)

        if isinstance(stmt, ExprStmt):
            return self._eval_expr(stmt.expr)

        if isinstance(stmt, ImportStmt):
            return self._eval_import(stmt)

        raise HaikuRuntimeError(f"Unknown statement type: {type(stmt).__name__}")

    def _eval_for(self, stmt: ForStmt) -> HValue:
        iterable = self._eval_expr(stmt.iterable)
        env = Environment(self.environment)
        previous = self.environment
        self.environment = env
        try:
            if isinstance(iterable, HList):
                items = iterable.elements
            elif isinstance(iterable, HMap):
                items = [h_string(k) for k in iterable.entries.keys()]
            elif isinstance(iterable, HString):
                items = [h_string(c) for c in iterable.value]
            else:
                raise HaikuRuntimeError(
                    f"Cannot iterate over {iterable.type}", stmt.line
                )

            for item in items:
                env.define(stmt.variable, item)
                try:
                    self._eval_stmt(stmt.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
        finally:
            self.environment = previous
        return h_none()

    def _eval_while(self, stmt: WhileStmt) -> HValue:
        while is_truthy(self._eval_expr(stmt.condition)):
            try:
                self._eval_stmt(stmt.body)
            except BreakException:
                break
            except ContinueException:
                continue
        return h_none()

    def _eval_try(self, stmt: TryStmt) -> HValue:
        try:
            for s in stmt.body:
                self._eval_stmt(s)
        except HaikuRuntimeError as e:
            if stmt.catch_body:
                env = Environment(self.environment)
                prev = self.environment
                self.environment = env
                try:
                    if stmt.catch_param:
                        # Provide the formatted traceback as the caught value
                        env.define(stmt.catch_param, h_string(e.message))
                    for s in stmt.catch_body:
                        self._eval_stmt(s)
                finally:
                    self.environment = prev
        finally:
            if stmt.finally_body:
                for s in stmt.finally_body:
                    self._eval_stmt(s)
        return h_none()

    def _eval_block(self, body: List[Stmt]) -> HValue:
        env = Environment(self.environment)
        prev = self.environment
        self.environment = env
        try:
            result: HValue = h_none()
            for stmt in body:
                result = self._eval_stmt(stmt)
            return result
        finally:
            self.environment = prev

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _eval_expr(self, expr: Expr) -> HValue:
        if isinstance(expr, Literal):
            v = expr.value
            if v is None:
                return h_none()
            if isinstance(v, bool):
                return h_bool(v)
            if isinstance(v, (int, float)):
                return h_number(float(v))
            return h_string(str(v))

        if isinstance(expr, Identifier):
            try:
                return self.environment.get(expr.name)
            except Exception as e:
                # Wrap NameError-style errors with line info
                raise HaikuRuntimeError(str(e), expr.line)

        if isinstance(expr, BinaryExpr):
            return self._eval_binary(expr)

        if isinstance(expr, UnaryExpr):
            return self._eval_unary(expr)

        if isinstance(expr, AssignExpr):
            return self._eval_assign(expr)

        if isinstance(expr, CallExpr):
            return self._eval_call(expr)

        if isinstance(expr, MemberExpr):
            return self._eval_member(expr)

        if isinstance(expr, IndexExpr):
            return self._eval_index(expr)

        if isinstance(expr, ListExpr):
            return h_list([self._eval_expr(e) for e in expr.elements])

        if isinstance(expr, MapExpr):
            entries: Dict[str, HValue] = {}
            for entry in expr.entries:
                key = self._eval_expr(entry.key)
                value = self._eval_expr(entry.value)
                entries[str(key)] = value
            return h_map(entries)

        if isinstance(expr, LambdaExpr):
            body = expr.body if isinstance(expr.body, list) else [ReturnStmt(expr.body)]
            fn = HFunction("<lambda>", expr.params, body, self.environment)
            fn.line = expr.line
            return fn

        if isinstance(expr, TernaryExpr):
            return self._eval_expr(expr.consequent) if is_truthy(self._eval_expr(expr.condition)) else self._eval_expr(expr.alternate)

        if isinstance(expr, ThisExpr):
            try:
                return self.environment.get("this")
            except Exception as e:
                raise HaikuRuntimeError(str(e), expr.line)

        if isinstance(expr, SuperExpr):
            this_val = self.environment.get("this")
            if not isinstance(this_val, HInstance):
                raise HaikuRuntimeError("'super' can only be used in class methods", expr.line)
            superclass = this_val.klass.superclass
            if not superclass:
                raise HaikuRuntimeError(
                    f"Class {this_val.klass.name} has no superclass", expr.line
                )
            method = superclass.methods.get(expr.method)
            if not method:
                raise HaikuRuntimeError(
                    f"Undefined method '{expr.method}' in superclass", expr.line
                )
            bound = HFunction(method.name, method.params, method.body, method.closure)
            bound.closure = Environment(method.closure)
            bound.closure.define("this", this_val)
            return bound

        if isinstance(expr, FString):
            return self._eval_fstring(expr)

        raise HaikuRuntimeError(f"Unknown expression type: {type(expr).__name__}")

    def _eval_binary(self, expr: BinaryExpr) -> HValue:
        left = self._eval_expr(expr.left)

        # Short-circuit
        if expr.operator == "&&":
            return left if not is_truthy(left) else self._eval_expr(expr.right)
        if expr.operator == "||":
            return left if is_truthy(left) else self._eval_expr(expr.right)

        right = self._eval_expr(expr.right)
        line = expr.line

        # Arithmetic
        if expr.operator == "+":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value + right.value)
            if isinstance(left, HString) or isinstance(right, HString):
                return h_string(str(left) + str(right))
            if isinstance(left, HList) and isinstance(right, HList):
                return h_list(left.elements + right.elements)
            raise HaikuRuntimeError(f"Cannot add {left.type} and {right.type}", line)

        if expr.operator == "-":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value - right.value)
            raise HaikuRuntimeError(f"Cannot subtract {right.type} from {left.type}", line)

        if expr.operator == "*":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value * right.value)
            if isinstance(left, HString) and isinstance(right, HNumber):
                return h_string(left.value * int(right.value))
            if isinstance(left, HNumber) and isinstance(right, HString):
                return h_string(right.value * int(left.value))
            raise HaikuRuntimeError(f"Cannot multiply {left.type} and {right.type}", line)

        if expr.operator == "/":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                if right.value == 0:
                    raise HaikuRuntimeError("Division by zero", line)
                return h_number(left.value / right.value)
            raise HaikuRuntimeError(f"Cannot divide {left.type} by {right.type}", line)

        if expr.operator == "%":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value % right.value)
            raise HaikuRuntimeError(f"Cannot modulo {left.type} by {right.type}", line)

        if expr.operator == "**":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value ** right.value)
            raise HaikuRuntimeError(f"Cannot power {left.type} and {right.type}", line)

        # Comparison
        if expr.operator == "==":
            return h_bool(self._values_equal(left, right))
        if expr.operator == "!=":
            return h_bool(not self._values_equal(left, right))
        if expr.operator == "<":
            return h_bool(self._compare(left, right, line) < 0)
        if expr.operator == ">":
            return h_bool(self._compare(left, right, line) > 0)
        if expr.operator == "<=":
            return h_bool(self._compare(left, right, line) <= 0)
        if expr.operator == ">=":
            return h_bool(self._compare(left, right, line) >= 0)

        # Bitwise
        if expr.operator == "&":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) & int(right.value))
            raise HaikuRuntimeError(f"Cannot bitwise-and {left.type} and {right.type}", line)
        if expr.operator == "|":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) | int(right.value))
            raise HaikuRuntimeError(f"Cannot bitwise-or {left.type} and {right.type}", line)
        if expr.operator == "^":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) ^ int(right.value))
            raise HaikuRuntimeError(f"Cannot bitwise-xor {left.type} and {right.type}", line)
        if expr.operator == "<<":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) << int(right.value))
            raise HaikuRuntimeError(f"Cannot left-shift {left.type} by {right.type}", line)
        if expr.operator == ">>":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) >> int(right.value))
            raise HaikuRuntimeError(f"Cannot right-shift {left.type} by {right.type}", line)

        # Range
        if expr.operator == "..":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_list([h_number(i) for i in range(int(left.value), int(right.value) + 1)])
            raise HaikuRuntimeError(f"Cannot create range from {left.type} to {right.type}", line)

        raise HaikuRuntimeError(f"Unknown operator {expr.operator}", line)

    def _eval_unary(self, expr: UnaryExpr) -> HValue:
        operand = self._eval_expr(expr.operand)
        line = expr.line
        if expr.operator in ("!", "not"):
            return h_bool(not is_truthy(operand))
        if expr.operator == "-":
            if isinstance(operand, HNumber):
                return h_number(-operand.value)
            raise HaikuRuntimeError(f"Cannot negate {operand.type}", line)
        if expr.operator == "~":
            if isinstance(operand, HNumber):
                return h_number(~int(operand.value))
            raise HaikuRuntimeError(f"Cannot bitwise-not {operand.type}", line)
        raise HaikuRuntimeError(f"Unknown unary operator {expr.operator}", line)

    def _eval_assign(self, expr: AssignExpr) -> HValue:
        value = self._eval_expr(expr.value)
        target = expr.target
        line = expr.line

        if isinstance(target, Identifier):
            try:
                self.environment.set(target.name, value)
            except Exception as e:
                raise HaikuRuntimeError(str(e), line)
        elif isinstance(target, MemberExpr):
            obj = self._eval_expr(target.obj)
            if isinstance(obj, HInstance):
                obj.fields[target.property] = value
            elif isinstance(obj, HMap):
                obj.entries[target.property] = value
            else:
                raise HaikuRuntimeError(f"Cannot set property on {obj.type}", line)
        elif isinstance(target, IndexExpr):
            obj = self._eval_expr(target.obj)
            index = self._eval_expr(target.index)
            if isinstance(obj, HList) and isinstance(index, HNumber):
                idx = int(index.value)
                if idx < 0 or idx >= len(obj.elements):
                    raise HaikuRuntimeError("Index out of bounds", line)
                obj.elements[idx] = value
            elif isinstance(obj, HMap) and isinstance(index, HString):
                obj.entries[index.value] = value
            else:
                raise HaikuRuntimeError(f"Cannot index-assign {obj.type}", line)
        return value

    def _eval_call(self, expr: CallExpr) -> HValue:
        callee = self._eval_expr(expr.callee)
        args = [self._eval_expr(a) for a in expr.args]
        line = expr.line

        if isinstance(callee, HNativeFn):
            if callee.arity >= 0 and len(args) != callee.arity:
                raise HaikuRuntimeError(
                    f"Expected {callee.arity} arguments but got {len(args)}", line
                )
            try:
                return callee.fn(args, self)
            except HaikuRuntimeError:
                raise
            except Exception as e:
                raise HaikuRuntimeError(str(e), line)

        if isinstance(callee, HFunction):
            return self._call_function(callee, args, call_line=line)

        if isinstance(callee, HClass):
            instance = HInstance(callee)
            init = callee.methods.get("init")
            if init:
                bound = HFunction(init.name, init.params, init.body, init.closure)
                bound.closure = Environment(init.closure)
                bound.closure.define("this", instance)
                bound.line = getattr(init, "line", 0)
                self._call_function(bound, args, call_line=line)
            return instance

        raise HaikuRuntimeError(f"Cannot call {callee.type}", line)

    def _call_function(self, fn: HFunction, args: List[HValue], call_line: int = 0) -> HValue:
        env = Environment(fn.closure)
        for i, param in enumerate(fn.params):
            if i < len(args):
                env.define(param.name, args[i])
            elif param.default:
                env.define(param.name, self._eval_expr(param.default))
            else:
                raise HaikuRuntimeError(
                    f"Missing argument for parameter '{param.name}'",
                    call_line
                )

        fn_name = fn.name if fn.name else "<lambda>"
        fn_def_line = getattr(fn, "line", 0)

        prev = self.environment
        self.environment = env
        try:
            for stmt in fn.body:
                self._eval_stmt(stmt)
            return h_none()
        except ReturnException as e:
            return e.value
        except HaikuRuntimeError as e:
            # Add this function's frame to the traceback
            label = f"fn '{fn_name}'" if fn_name != "<lambda>" else "<lambda>"
            e.push_frame(label, call_line)
            raise
        finally:
            self.environment = prev

    def _eval_member(self, expr: MemberExpr) -> HValue:
        obj = self._eval_expr(expr.obj)
        line = expr.line

        if expr.optional and isinstance(obj, HNone):
            return h_none()

        if isinstance(obj, HInstance):
            val = obj.get(expr.property)
            if val is not None:
                return val
            raise HaikuRuntimeError(
                f"Undefined property '{expr.property}' on instance of {obj.klass.name}", line
            )

        if isinstance(obj, HClass):
            static = obj.static_methods.get(expr.property)
            if static:
                return static
            raise HaikuRuntimeError(
                f"Undefined static member '{expr.property}' on class {obj.name}", line
            )

        if isinstance(obj, HModule):
            val = obj.get(expr.property)
            if val is not None:
                return val
            raise HaikuRuntimeError(f"Module has no export '{expr.property}'", line)

        # Native methods (check before map entries so methods like .keys() work)
        method = self._get_native_method(obj, expr.property)
        if method:
            return method

        if isinstance(obj, HMap):
            val = obj.entries.get(expr.property)
            if val is not None:
                return val
            return h_none()

        raise HaikuRuntimeError(
            f"Cannot access property '{expr.property}' on {obj.type}", line
        )

    def _eval_index(self, expr: IndexExpr) -> HValue:
        obj = self._eval_expr(expr.obj)
        index = self._eval_expr(expr.index)
        line = expr.line

        if isinstance(obj, HList) and isinstance(index, HNumber):
            idx = int(index.value)
            if idx < 0 or idx >= len(obj.elements):
                raise HaikuRuntimeError("Index out of bounds", line)
            return obj.elements[idx]

        if isinstance(obj, HString) and isinstance(index, HNumber):
            idx = int(index.value)
            if idx < 0 or idx >= len(obj.value):
                raise HaikuRuntimeError("Index out of bounds", line)
            return h_string(obj.value[idx])

        if isinstance(obj, HMap) and isinstance(index, HString):
            val = obj.entries.get(index.value)
            if val is not None:
                return val
            return h_none()

        raise HaikuRuntimeError(f"Cannot index {obj.type} with {index.type}", line)

    # ------------------------------------------------------------------
    # Native methods
    # ------------------------------------------------------------------

    def _get_native_method(self, obj: HValue, name: str) -> Optional[HNativeFn]:
        if isinstance(obj, HString):
            return self._string_method(obj, name)
        if isinstance(obj, HList):
            return self._list_method(obj, name)
        if isinstance(obj, HMap):
            return self._map_method(obj, name)
        return None

    def _string_method(self, s: HString, name: str) -> Optional[HNativeFn]:
        methods = {
            "len": lambda args, _: h_number(len(s.value)),
            "upper": lambda args, _: h_string(s.value.upper()),
            "lower": lambda args, _: h_string(s.value.lower()),
            "trim": lambda args, _: h_string(s.value.strip()),
            "split": lambda args, _: h_list([h_string(x) for x in s.value.split(args[0].value if args and isinstance(args[0], HString) else " ")]),
            "contains": lambda args, _: h_bool(args[0].value in s.value if args and isinstance(args[0], HString) else False),
            "replace": lambda args, _: h_string(s.value.replace(args[0].value, args[1].value)) if len(args) >= 2 and isinstance(args[0], HString) and isinstance(args[1], HString) else s,
            "startsWith": lambda args, _: h_bool(s.value.startswith(args[0].value)) if args and isinstance(args[0], HString) else h_bool(False),
            "endsWith": lambda args, _: h_bool(s.value.endswith(args[0].value)) if args and isinstance(args[0], HString) else h_bool(False),
            "slice": lambda args, _: h_string(s.value[int(args[0].value) if args and isinstance(args[0], HNumber) else 0:int(args[1].value) if len(args) > 1 and isinstance(args[1], HNumber) else len(s.value)]),
        }
        if name in methods:
            return HNativeFn(name, -1, methods[name])
        return None

    def _list_method(self, lst: HList, name: str) -> Optional[HNativeFn]:
        methods = {
            "len": lambda args, _: h_number(len(lst.elements)),
            "push": lambda args, _: self._list_push(lst, args),
            "pop": lambda args, _: lst.elements.pop() if lst.elements else h_none(),
            "shift": lambda args, _: lst.elements.pop(0) if lst.elements else h_none(),
            "unshift": lambda args, _: self._list_unshift(lst, args),
            "get": lambda args, _: lst.elements[int(args[0].value)] if args and isinstance(args[0], HNumber) and 0 <= int(args[0].value) < len(lst.elements) else h_none(),
            "set": lambda args, _: self._list_set(lst, args),
            "contains": lambda args, _: h_bool(any(self._values_equal(e, args[0]) for e in lst.elements)),
            "find": lambda args, _: self._list_find(lst, args),
            "filter": lambda args, _: self._list_filter(lst, args),
            "map": lambda args, _: self._list_map(lst, args),
            "reduce": lambda args, _: self._list_reduce(lst, args),
            "sort": lambda args, _: h_list(sorted(lst.elements, key=lambda x: x.value if isinstance(x, (HNumber, HString)) else 0)),
            "reverse": lambda args, _: h_list(lst.elements[::-1]),
            "join": lambda args, _: h_string((args[0].value if args and isinstance(args[0], HString) else ",").join(str(e) for e in lst.elements)),
            "slice": lambda args, _: h_list(lst.elements[int(args[0].value) if args and isinstance(args[0], HNumber) else 0:int(args[1].value) if len(args) > 1 and isinstance(args[1], HNumber) else len(lst.elements)]),
        }
        if name in methods:
            return HNativeFn(name, -1, methods[name])
        return None

    def _list_push(self, lst: HList, args: List[HValue]) -> HValue:
        lst.elements.extend(args)
        return h_none()

    def _list_unshift(self, lst: HList, args: List[HValue]) -> HValue:
        for arg in reversed(args):
            lst.elements.insert(0, arg)
        return h_none()

    def _list_set(self, lst: HList, args: List[HValue]) -> HValue:
        if args and isinstance(args[0], HNumber):
            idx = int(args[0].value)
            if 0 <= idx < len(lst.elements):
                lst.elements[idx] = args[1] if len(args) > 1 else h_none()
        return h_none()

    def _list_find(self, lst: HList, args: List[HValue]) -> HValue:
        if args and isinstance(args[0], HFunction):
            for el in lst.elements:
                if is_truthy(self._call_function(args[0], [el])):
                    return el
        return h_none()

    def _list_filter(self, lst: HList, args: List[HValue]) -> HValue:
        if args and isinstance(args[0], HFunction):
            return h_list([el for el in lst.elements if is_truthy(self._call_function(args[0], [el]))])
        return h_list([])

    def _list_map(self, lst: HList, args: List[HValue]) -> HValue:
        if args and isinstance(args[0], HFunction):
            return h_list([self._call_function(args[0], [el]) for el in lst.elements])
        return h_list([])

    def _list_reduce(self, lst: HList, args: List[HValue]) -> HValue:
        if args and isinstance(args[0], HFunction):
            acc = args[1] if len(args) > 1 else h_none()
            for el in lst.elements:
                acc = self._call_function(args[0], [acc, el])
            return acc
        return h_none()

    def _map_method(self, m: HMap, name: str) -> Optional[HNativeFn]:
        methods = {
            "len": lambda args, _: h_number(len(m.entries)),
            "keys": lambda args, _: h_list([h_string(k) for k in m.entries.keys()]),
            "values": lambda args, _: h_list(list(m.entries.values())),
            "entries": lambda args, _: h_list([h_list([h_string(k), v]) for k, v in m.entries.items()]),
            "has": lambda args, _: h_bool(args[0].value in m.entries) if args and isinstance(args[0], HString) else h_bool(False),
            "delete": lambda args, _: self._map_delete(m, args),
            "clear": lambda args, _: self._map_clear(m),
        }
        if name in methods:
            return HNativeFn(name, -1, methods[name])
        return None

    def _map_delete(self, m: HMap, args: List[HValue]) -> HValue:
        if args and isinstance(args[0], HString):
            m.entries.pop(args[0].value, None)
        return h_none()

    def _map_clear(self, m: HMap) -> HValue:
        m.entries.clear()
        return h_none()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _values_equal(self, a: HValue, b: HValue) -> bool:
        if a.type != b.type:
            return False
        if isinstance(a, HNumber) and isinstance(b, HNumber):
            return a.value == b.value
        if isinstance(a, HString) and isinstance(b, HString):
            return a.value == b.value
        if isinstance(a, HBoolean) and isinstance(b, HBoolean):
            return a.value == b.value
        if isinstance(a, HNone) and isinstance(b, HNone):
            return True
        if isinstance(a, HList) and isinstance(b, HList):
            if len(a.elements) != len(b.elements):
                return False
            return all(self._values_equal(x, y) for x, y in zip(a.elements, b.elements))
        if isinstance(a, HMap) and isinstance(b, HMap):
            if len(a.entries) != len(b.entries):
                return False
            for k, v in a.entries.items():
                bv = b.entries.get(k)
                if bv is None or not self._values_equal(v, bv):
                    return False
            return True
        return a is b

    def _compare(self, a: HValue, b: HValue, line: int = 0) -> float:
        if isinstance(a, HNumber) and isinstance(b, HNumber):
            return a.value - b.value
        if isinstance(a, HString) and isinstance(b, HString):
            return -1 if a.value < b.value else (1 if a.value > b.value else 0)
        raise HaikuRuntimeError(f"Cannot compare {a.type} and {b.type}", line)

    def _eval_fstring(self, expr: FString) -> HValue:
        """Evaluate an f-string by interpolating expressions."""
        result = ""
        for part in expr.parts:
            if isinstance(part, str):
                result += part
            else:
                value = self._eval_expr(part)
                result += str(value)
        return h_string(result)

    def _eval_import(self, stmt: ImportStmt) -> HValue:
        """Evaluate import statement."""
        import os

        if stmt.path:
            # Import from .hku file
            path = stmt.path
            if not path.endswith('.hku'):
                path += '.hku'

            # Resolve path relative to current file or working directory
            if not os.path.isabs(path):
                # Try to find the file
                for search_dir in [os.getcwd(), 'examples', 'lib']:
                    full_path = os.path.join(search_dir, path)
                    if os.path.exists(full_path):
                        path = full_path
                        break

            if not os.path.exists(path):
                raise HaikuRuntimeError(f"Import file not found: {path}", stmt.line)

            # Read and execute the file
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()

            # Parse and execute the imported file
            from .lexer import Lexer
            from .parser import Parser
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()

            # Execute in a new environment
            import_env = Environment(self.globals)
            previous = self.environment
            self.environment = import_env
            try:
                self.interpret(ast)
            finally:
                self.environment = previous

            # Export the requested names
            module = HModule(stmt.alias or path, import_env)
            if stmt.names:
                for name in stmt.names:
                    if name == '*':
                        # Export all
                        for key, value in import_env.values.items():
                            self.environment.define(key, value)
                    else:
                        value = import_env.get(name)
                        self.environment.define(name, value)
            else:
                # Import the whole module
                module_name = stmt.alias or os.path.splitext(os.path.basename(path))[0]
                self.environment.define(module_name, module)
        else:
            # Import built-in module (Math, Time, JSON, File)
            module_name = stmt.names[0] if stmt.names else ''
            if module_name in ['Math', 'Time', 'JSON', 'File']:
                # These are already in the global environment from stdlib
                value = self.globals.get(module_name)
                alias = stmt.alias or module_name
                self.environment.define(alias, value)
            else:
                raise HaikuRuntimeError(f"Unknown built-in module: {module_name}", stmt.line)

        return h_none()
