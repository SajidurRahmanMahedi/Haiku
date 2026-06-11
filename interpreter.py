"""
Haiku Interpreter
=================
Tree-walking interpreter that executes the AST produced by the parser.
Supports functions, closures, classes, inheritance, exceptions, and
all built-in operations.
"""

from typing import List, Optional, Dict, Any
from ast_nodes import (
    Program, Stmt, Expr, VarDecl, FnDecl, ClassDecl, IfStmt, ForStmt,
    WhileStmt, MatchStmt, TryStmt, ThrowStmt, ReturnStmt, BreakStmt,
    ContinueStmt, Block, ExprStmt, ImportStmt, Literal, Identifier,
    BinaryExpr, UnaryExpr, AssignExpr, CallExpr, MemberExpr, IndexExpr,
    ListExpr, MapExpr, MapEntry, LambdaExpr, TernaryExpr, ThisExpr, SuperExpr
)
from values import (
    HValue, HNumber, HString, HBoolean, HNone, HList, HMap,
    HFunction, HClass, HInstance, HNativeFn, HModule,
    Environment, is_truthy, h_number, h_string, h_bool, h_none, h_list, h_map
)


class ReturnException(Exception):
    def __init__(self, value: HValue):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class RuntimeError(Exception):
    pass


class Interpreter:
    """Executes Haiku AST nodes."""

    def __init__(self, globals: Optional[Environment] = None):
        self.globals = globals or Environment()
        self.environment = self.globals
        self.output_buffer: List[str] = []
        self.input_provider: Optional[callable] = None

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
    # Statements
    # ------------------------------------------------------------------

    def _eval_stmt(self, stmt: Stmt) -> HValue:
        if isinstance(stmt, VarDecl):
            value = self._eval_expr(stmt.init) if stmt.init else h_none()
            self.environment.define(stmt.name, value)
            return value

        if isinstance(stmt, FnDecl):
            fn = HFunction(stmt.name, stmt.params, stmt.body, self.environment)
            self.environment.define(stmt.name, fn)
            return fn

        if isinstance(stmt, ClassDecl):
            superclass = None
            if stmt.superclass:
                sup = self.environment.get(stmt.superclass.name)
                if not isinstance(sup, HClass):
                    raise RuntimeError(f"Superclass {stmt.superclass.name} is not a class")
                superclass = sup

            methods: Dict[str, HFunction] = {}
            static_methods: Dict[str, HFunction] = {}
            for method in stmt.methods:
                fn = HFunction(method.name, method.params, method.body, self.environment)
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
            raise RuntimeError(str(value))

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
            return h_none()

        raise RuntimeError(f"Unknown statement type: {type(stmt).__name__}")

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
                raise RuntimeError(f"Cannot iterate over {iterable.type}")

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
        except RuntimeError as e:
            if stmt.catch_body:
                env = Environment(self.environment)
                prev = self.environment
                self.environment = env
                try:
                    if stmt.catch_param:
                        env.define(stmt.catch_param, h_string(str(e)))
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
            return self.environment.get(expr.name)

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
            return HFunction("<lambda>", expr.params, body, self.environment)

        if isinstance(expr, TernaryExpr):
            return self._eval_expr(expr.consequent) if is_truthy(self._eval_expr(expr.condition)) else self._eval_expr(expr.alternate)

        if isinstance(expr, ThisExpr):
            return self.environment.get("this")

        if isinstance(expr, SuperExpr):
            this_val = self.environment.get("this")
            if not isinstance(this_val, HInstance):
                raise RuntimeError("'super' can only be used in class methods")
            superclass = this_val.klass.superclass
            if not superclass:
                raise RuntimeError(f"Class {this_val.klass.name} has no superclass")
            method = superclass.methods.get(expr.method)
            if not method:
                raise RuntimeError(f"Undefined method '{expr.method}' in superclass")
            bound = HFunction(method.name, method.params, method.body, method.closure)
            bound.closure = Environment(method.closure)
            bound.closure.define("this", this_val)
            return bound

        raise RuntimeError(f"Unknown expression type: {type(expr).__name__}")

    def _eval_binary(self, expr: BinaryExpr) -> HValue:
        left = self._eval_expr(expr.left)

        # Short-circuit
        if expr.operator == "&&":
            return left if not is_truthy(left) else self._eval_expr(expr.right)
        if expr.operator == "||":
            return left if is_truthy(left) else self._eval_expr(expr.right)

        right = self._eval_expr(expr.right)

        # Arithmetic
        if expr.operator == "+":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value + right.value)
            if isinstance(left, HString) or isinstance(right, HString):
                return h_string(str(left) + str(right))
            if isinstance(left, HList) and isinstance(right, HList):
                return h_list(left.elements + right.elements)
            raise RuntimeError(f"Cannot add {left.type} and {right.type}")

        if expr.operator == "-":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value - right.value)
            raise RuntimeError(f"Cannot subtract {right.type} from {left.type}")

        if expr.operator == "*":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value * right.value)
            if isinstance(left, HString) and isinstance(right, HNumber):
                return h_string(left.value * int(right.value))
            if isinstance(left, HNumber) and isinstance(right, HString):
                return h_string(right.value * int(left.value))
            raise RuntimeError(f"Cannot multiply {left.type} and {right.type}")

        if expr.operator == "/":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                if right.value == 0:
                    raise RuntimeError("Division by zero")
                return h_number(left.value / right.value)
            raise RuntimeError(f"Cannot divide {left.type} by {right.type}")

        if expr.operator == "%":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value % right.value)
            raise RuntimeError(f"Cannot modulo {left.type} by {right.type}")

        if expr.operator == "**":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(left.value ** right.value)
            raise RuntimeError(f"Cannot power {left.type} and {right.type}")

        # Comparison
        if expr.operator == "==":
            return h_bool(self._values_equal(left, right))
        if expr.operator == "!=":
            return h_bool(not self._values_equal(left, right))
        if expr.operator == "<":
            return h_bool(self._compare(left, right) < 0)
        if expr.operator == ">":
            return h_bool(self._compare(left, right) > 0)
        if expr.operator == "<=":
            return h_bool(self._compare(left, right) <= 0)
        if expr.operator == ">=":
            return h_bool(self._compare(left, right) >= 0)

        # Bitwise
        if expr.operator == "&":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) & int(right.value))
            raise RuntimeError(f"Cannot bitwise-and {left.type} and {right.type}")
        if expr.operator == "|":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) | int(right.value))
            raise RuntimeError(f"Cannot bitwise-or {left.type} and {right.type}")
        if expr.operator == "^":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) ^ int(right.value))
            raise RuntimeError(f"Cannot bitwise-xor {left.type} and {right.type}")
        if expr.operator == "<<":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) << int(right.value))
            raise RuntimeError(f"Cannot left-shift {left.type} by {right.type}")
        if expr.operator == ">>":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_number(int(left.value) >> int(right.value))
            raise RuntimeError(f"Cannot right-shift {left.type} by {right.type}")

        # Range
        if expr.operator == "..":
            if isinstance(left, HNumber) and isinstance(right, HNumber):
                return h_list([h_number(i) for i in range(int(left.value), int(right.value) + 1)])
            raise RuntimeError(f"Cannot create range from {left.type} to {right.type}")

        raise RuntimeError(f"Unknown operator {expr.operator}")

    def _eval_unary(self, expr: UnaryExpr) -> HValue:
        operand = self._eval_expr(expr.operand)
        if expr.operator in ("!", "not"):
            return h_bool(not is_truthy(operand))
        if expr.operator == "-":
            if isinstance(operand, HNumber):
                return h_number(-operand.value)
            raise RuntimeError(f"Cannot negate {operand.type}")
        if expr.operator == "~":
            if isinstance(operand, HNumber):
                return h_number(~int(operand.value))
            raise RuntimeError(f"Cannot bitwise-not {operand.type}")
        raise RuntimeError(f"Unknown unary operator {expr.operator}")

    def _eval_assign(self, expr: AssignExpr) -> HValue:
        value = self._eval_expr(expr.value)
        target = expr.target

        if isinstance(target, Identifier):
            self.environment.set(target.name, value)
        elif isinstance(target, MemberExpr):
            obj = self._eval_expr(target.obj)
            if isinstance(obj, HInstance):
                obj.fields[target.property] = value
            elif isinstance(obj, HMap):
                obj.entries[target.property] = value
            else:
                raise RuntimeError(f"Cannot set property on {obj.type}")
        elif isinstance(target, IndexExpr):
            obj = self._eval_expr(target.obj)
            index = self._eval_expr(target.index)
            if isinstance(obj, HList) and isinstance(index, HNumber):
                idx = int(index.value)
                if idx < 0 or idx >= len(obj.elements):
                    raise RuntimeError("Index out of bounds")
                obj.elements[idx] = value
            elif isinstance(obj, HMap) and isinstance(index, HString):
                obj.entries[index.value] = value
            else:
                raise RuntimeError(f"Cannot index-assign {obj.type}")
        return value

    def _eval_call(self, expr: CallExpr) -> HValue:
        callee = self._eval_expr(expr.callee)
        args = [self._eval_expr(a) for a in expr.args]

        if isinstance(callee, HNativeFn):
            if callee.arity >= 0 and len(args) != callee.arity:
                raise RuntimeError(f"Expected {callee.arity} arguments but got {len(args)}")
            return callee.fn(args, self)

        if isinstance(callee, HFunction):
            return self._call_function(callee, args)

        if isinstance(callee, HClass):
            instance = HInstance(callee)
            init = callee.methods.get("init")
            if init:
                bound = HFunction(init.name, init.params, init.body, init.closure)
                bound.closure = Environment(init.closure)
                bound.closure.define("this", instance)
                self._call_function(bound, args)
            return instance

        raise RuntimeError(f"Cannot call {callee.type}")

    def _call_function(self, fn: HFunction, args: List[HValue]) -> HValue:
        env = Environment(fn.closure)
        for i, param in enumerate(fn.params):
            if i < len(args):
                env.define(param.name, args[i])
            elif param.default:
                env.define(param.name, self._eval_expr(param.default))
            else:
                raise RuntimeError(f"Missing argument for parameter '{param.name}'")

        prev = self.environment
        self.environment = env
        try:
            for stmt in fn.body:
                self._eval_stmt(stmt)
            return h_none()
        except ReturnException as e:
            return e.value
        finally:
            self.environment = prev

    def _eval_member(self, expr: MemberExpr) -> HValue:
        obj = self._eval_expr(expr.obj)

        if expr.optional and isinstance(obj, HNone):
            return h_none()

        if isinstance(obj, HInstance):
            val = obj.get(expr.property)
            if val is not None:
                return val
            raise RuntimeError(f"Undefined property '{expr.property}' on instance of {obj.klass.name}")

        if isinstance(obj, HClass):
            static = obj.static_methods.get(expr.property)
            if static:
                return static
            raise RuntimeError(f"Undefined static member '{expr.property}' on class {obj.name}")

        if isinstance(obj, HModule):
            val = obj.get(expr.property)
            if val is not None:
                return val
            raise RuntimeError(f"Module has no export '{expr.property}'")

        # Native methods (check before map entries so methods like .keys() work)
        method = self._get_native_method(obj, expr.property)
        if method:
            return method

        if isinstance(obj, HMap):
            val = obj.entries.get(expr.property)
            if val is not None:
                return val
            return h_none()

        raise RuntimeError(f"Cannot access property '{expr.property}' on {obj.type}")

    def _eval_index(self, expr: IndexExpr) -> HValue:
        obj = self._eval_expr(expr.obj)
        index = self._eval_expr(expr.index)

        if isinstance(obj, HList) and isinstance(index, HNumber):
            idx = int(index.value)
            if idx < 0 or idx >= len(obj.elements):
                raise RuntimeError("Index out of bounds")
            return obj.elements[idx]

        if isinstance(obj, HString) and isinstance(index, HNumber):
            idx = int(index.value)
            if idx < 0 or idx >= len(obj.value):
                raise RuntimeError("Index out of bounds")
            return h_string(obj.value[idx])

        if isinstance(obj, HMap) and isinstance(index, HString):
            val = obj.entries.get(index.value)
            if val is not None:
                return val
            return h_none()

        raise RuntimeError(f"Cannot index {obj.type} with {index.type}")

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

    def _compare(self, a: HValue, b: HValue) -> float:
        if isinstance(a, HNumber) and isinstance(b, HNumber):
            return a.value - b.value
        if isinstance(a, HString) and isinstance(b, HString):
            return -1 if a.value < b.value else (1 if a.value > b.value else 0)
        raise RuntimeError(f"Cannot compare {a.type} and {b.type}")
