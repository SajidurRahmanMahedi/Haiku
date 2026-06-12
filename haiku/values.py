"""
Haiku Runtime Values
====================
All values that exist at runtime are instances of HValue subclasses.
This includes primitives, collections, functions, classes, and instances.
"""

from typing import List, Dict, Callable, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .interpreter import Interpreter


class HValue:
    """Base class for all Haiku runtime values."""
    def __init__(self, type_name: str):
        self.type = type_name

    def __str__(self) -> str:
        return f"<{self.type}>"

    def __repr__(self) -> str:
        return self.__str__()


class HNumber(HValue):
    def __init__(self, value: float):
        super().__init__("number")
        self.value = value

    def __str__(self) -> str:
        if self.value == int(self.value):
            return str(int(self.value))
        return str(self.value)


class HString(HValue):
    def __init__(self, value: str):
        super().__init__("string")
        self.value = value

    def __str__(self) -> str:
        return self.value


class HBoolean(HValue):
    def __init__(self, value: bool):
        super().__init__("boolean")
        self.value = value

    def __str__(self) -> str:
        return "true" if self.value else "false"


class HNone(HValue):
    def __init__(self):
        super().__init__("none")

    def __str__(self) -> str:
        return "none"


class HList(HValue):
    def __init__(self, elements: List[HValue]):
        super().__init__("list")
        self.elements = elements

    def __str__(self) -> str:
        return "[" + ", ".join(str(e) for e in self.elements) + "]"


class HMap(HValue):
    def __init__(self, entries: Dict[str, HValue]):
        super().__init__("map")
        self.entries = entries

    def __str__(self) -> str:
        items = [f"{k}: {v}" for k, v in self.entries.items()]
        return "{" + ", ".join(items) + "}"


class HFunction(HValue):
    def __init__(self, name: str, params: List[Any], body: List[Any],
                 closure: "Environment", is_async: bool = False):
        super().__init__("function")
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure
        self.is_async = is_async

    def __str__(self) -> str:
        return f"<fn {self.name}>"


class HClass(HValue):
    def __init__(self, name: str, superclass: Optional["HClass"],
                 methods: Dict[str, HFunction], static_methods: Dict[str, HFunction]):
        super().__init__("class")
        self.name = name
        self.superclass = superclass
        self.methods = methods
        self.static_methods = static_methods

    def __str__(self) -> str:
        return f"<class {self.name}>"


class HInstance(HValue):
    def __init__(self, klass: HClass):
        super().__init__("instance")
        self.klass = klass
        self.fields: Dict[str, HValue] = {}

    def __str__(self) -> str:
        return f"<instance of {self.klass.name}>"

    def get(self, name: str) -> Optional[HValue]:
        if name in self.fields:
            return self.fields[name]
        method = self.klass.methods.get(name)
        if method:
            bound = HFunction(method.name, method.params, method.body, method.closure)
            bound.closure = Environment(method.closure)
            bound.closure.define("this", self)
            return bound
        return None


class HNativeFn(HValue):
    def __init__(self, name: str, arity: int,
                 fn: Callable[[List[HValue], "Interpreter"], HValue]):
        super().__init__("native")
        self.name = name
        self.arity = arity
        self.fn = fn

    def __str__(self) -> str:
        return f"<native fn {self.name}>"


class HModule(HValue):
    def __init__(self, name: str, exports: "Environment"):
        super().__init__("module")
        self.name = name
        self.exports = exports

    def __str__(self) -> str:
        return f"<module {self.name}>"

    def get(self, name: str) -> Optional[HValue]:
        try:
            return self.exports.get(name)
        except RuntimeError:
            return None


class Environment:
    """Variable scope environment with enclosing parent support."""

    def __init__(self, enclosing: Optional["Environment"] = None):
        self.values: Dict[str, HValue] = {}
        self.enclosing = enclosing

    def define(self, name: str, value: HValue):
        self.values[name] = value

    def get(self, name: str) -> HValue:
        if name in self.values:
            return self.values[name]
        if self.enclosing:
            return self.enclosing.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def set(self, name: str, value: HValue):
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing:
            self.enclosing.set(name, value)
            return
        raise RuntimeError(f"Undefined variable '{name}'")

    def has(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.enclosing:
            return self.enclosing.has(name)
        return False


def is_truthy(value: HValue) -> bool:
    if isinstance(value, HNone):
        return False
    if isinstance(value, HBoolean):
        return value.value
    if isinstance(value, HNumber):
        return value.value != 0
    if isinstance(value, HString):
        return len(value.value) > 0
    if isinstance(value, HList):
        return len(value.elements) > 0
    if isinstance(value, HMap):
        return len(value.entries) > 0
    return True


def h_number(value: float) -> HNumber:
    return HNumber(value)


def h_string(value: str) -> HString:
    return HString(value)


def h_bool(value: bool) -> HBoolean:
    return HBoolean(value)


def h_none() -> HNone:
    return HNone()


def h_list(elements: List[HValue]) -> HList:
    return HList(elements)


def h_map(entries: Dict[str, HValue]) -> HMap:
    return HMap(entries)
