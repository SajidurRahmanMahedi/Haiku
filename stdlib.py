"""
Haiku Standard Library
======================
Built-in functions and modules available to all Haiku programs.
Includes I/O, math, time, JSON, file operations, and type utilities.
"""

import math
import random
import json as pyjson
from typing import Dict, List
from values import (
    Environment, HNativeFn, HNumber, HString, HBoolean, HNone,
    HList, HMap, HModule, HValue, h_number, h_string, h_bool, h_none, h_list, h_map
)


def _json_to_hvalue(data) -> HValue:
    """Convert Python JSON data to Haiku values."""
    if data is None:
        return h_none()
    if isinstance(data, bool):
        return h_bool(data)
    if isinstance(data, (int, float)):
        return h_number(float(data))
    if isinstance(data, str):
        return h_string(data)
    if isinstance(data, list):
        return h_list([_json_to_hvalue(x) for x in data])
    if isinstance(data, dict):
        return h_map({k: _json_to_hvalue(v) for k, v in data.items()})
    return h_none()


def _hvalue_to_json(value: HValue):
    """Convert Haiku values to Python JSON data."""
    if isinstance(value, HNone):
        return None
    if isinstance(value, HBoolean):
        return value.value
    if isinstance(value, HNumber):
        return value.value
    if isinstance(value, HString):
        return value.value
    if isinstance(value, HList):
        return [_hvalue_to_json(x) for x in value.elements]
    if isinstance(value, HMap):
        return {k: _hvalue_to_json(v) for k, v in value.entries.items()}
    return str(value)


def create_global_env(interpreter) -> Environment:
    """Create the global environment with all built-ins."""
    env = Environment()

    # ------------------------------------------------------------------
    # I/O Functions
    # ------------------------------------------------------------------

    def _print(args, interp):
        text = " ".join(str(a) for a in args)
        interp.write(text)
        return h_none()

    def _println(args, interp):
        text = " ".join(str(a) for a in args)
        interp.writeln(text)
        return h_none()

    def _input_fn(args, interp):
        if args:
            interp.write(str(args[0]))
        return h_string(interp.read_input())

    env.define("print", HNativeFn("print", -1, _print))
    env.define("println", HNativeFn("println", -1, _println))
    env.define("input", HNativeFn("input", 1, _input_fn))

    # ------------------------------------------------------------------
    # Type Functions
    # ------------------------------------------------------------------

    env.define("type", HNativeFn("type", 1, lambda args, _: h_string(args[0].type)))

    def _len_fn(args, _):
        arg = args[0]
        if isinstance(arg, HString):
            return h_number(len(arg.value))
        if isinstance(arg, HList):
            return h_number(len(arg.elements))
        if isinstance(arg, HMap):
            return h_number(len(arg.entries))
        raise RuntimeError(f"Cannot get length of {arg.type}")

    env.define("len", HNativeFn("len", 1, _len_fn))
    env.define("str", HNativeFn("str", 1, lambda args, _: h_string(str(args[0]))))

    def _int_fn(args, _):
        arg = args[0]
        if isinstance(arg, HNumber):
            return h_number(int(arg.value))
        if isinstance(arg, HString):
            return h_number(int(arg.value) if arg.value.isdigit() or (arg.value.startswith("-") and arg.value[1:].isdigit()) else 0)
        if isinstance(arg, HBoolean):
            return h_number(1 if arg.value else 0)
        return h_number(0)

    def _float_fn(args, _):
        arg = args[0]
        if isinstance(arg, HNumber):
            return arg
        if isinstance(arg, HString):
            try:
                return h_number(float(arg.value))
            except ValueError:
                return h_number(0)
        if isinstance(arg, HBoolean):
            return h_number(1.0 if arg.value else 0.0)
        return h_number(0)

    def _bool_fn(args, _):
        arg = args[0]
        if isinstance(arg, HNone):
            return h_bool(False)
        if isinstance(arg, HBoolean):
            return arg
        if isinstance(arg, HNumber):
            return h_bool(arg.value != 0)
        if isinstance(arg, HString):
            return h_bool(len(arg.value) > 0)
        if isinstance(arg, HList):
            return h_bool(len(arg.elements) > 0)
        if isinstance(arg, HMap):
            return h_bool(len(arg.entries) > 0)
        return h_bool(True)

    env.define("int", HNativeFn("int", 1, _int_fn))
    env.define("float", HNativeFn("float", 1, _float_fn))
    env.define("bool", HNativeFn("bool", 1, _bool_fn))

    # ------------------------------------------------------------------
    # Range
    # ------------------------------------------------------------------

    def _range_fn(args, _):
        start, end, step = 0, 0, 1
        if len(args) == 1:
            end = int(args[0].value)
        elif len(args) == 2:
            start = int(args[0].value)
            end = int(args[1].value)
        elif len(args) >= 3:
            start = int(args[0].value)
            end = int(args[1].value)
            step = int(args[2].value)

        if step > 0:
            return h_list([h_number(i) for i in range(start, end, step)])
        elif step < 0:
            return h_list([h_number(i) for i in range(start, end, step)])
        return h_list([])

    env.define("range", HNativeFn("range", -1, _range_fn))

    # ------------------------------------------------------------------
    # Math Module
    # ------------------------------------------------------------------

    math_env = Environment()
    math_env.define("abs", HNativeFn("abs", 1, lambda args, _: h_number(abs(args[0].value))))
    math_env.define("sin", HNativeFn("sin", 1, lambda args, _: h_number(math.sin(args[0].value))))
    math_env.define("cos", HNativeFn("cos", 1, lambda args, _: h_number(math.cos(args[0].value))))
    math_env.define("tan", HNativeFn("tan", 1, lambda args, _: h_number(math.tan(args[0].value))))
    math_env.define("sqrt", HNativeFn("sqrt", 1, lambda args, _: h_number(math.sqrt(args[0].value))))
    math_env.define("pow", HNativeFn("pow", 2, lambda args, _: h_number(args[0].value ** args[1].value)))
    math_env.define("log", HNativeFn("log", 1, lambda args, _: h_number(math.log(args[0].value))))
    math_env.define("log10", HNativeFn("log10", 1, lambda args, _: h_number(math.log10(args[0].value))))
    math_env.define("exp", HNativeFn("exp", 1, lambda args, _: h_number(math.exp(args[0].value))))
    math_env.define("floor", HNativeFn("floor", 1, lambda args, _: h_number(math.floor(args[0].value))))
    math_env.define("ceil", HNativeFn("ceil", 1, lambda args, _: h_number(math.ceil(args[0].value))))
    math_env.define("round", HNativeFn("round", 1, lambda args, _: h_number(round(args[0].value))))
    math_env.define("max", HNativeFn("max", -1, lambda args, _: h_number(max(a.value for a in args if isinstance(a, HNumber)))))
    math_env.define("min", HNativeFn("min", -1, lambda args, _: h_number(min(a.value for a in args if isinstance(a, HNumber)))))
    math_env.define("random", HNativeFn("random", 0, lambda args, _: h_number(random.random())))
    math_env.define("randint", HNativeFn("randint", 2, lambda args, _: h_number(random.randint(int(args[0].value), int(args[1].value)))))
    math_env.define("PI", h_number(math.pi))
    math_env.define("E", h_number(math.e))
    math_env.define("TAU", h_number(math.tau))

    # ------------------------------------------------------------------
    # Time Module
    # ------------------------------------------------------------------

    time_env = Environment()
    time_env.define("now", HNativeFn("now", 0, lambda args, _: h_number(__import__("time").time() * 1000)))

    def _sleep_fn(args, _):
        import time
        ms = args[0].value if args and isinstance(args[0], HNumber) else 0
        time.sleep(ms / 1000)
        return h_none()

    time_env.define("sleep", HNativeFn("sleep", 1, _sleep_fn))

    def _format_fn(args, _):
        from datetime import datetime
        timestamp = args[0].value / 1000 if args and isinstance(args[0], HNumber) else __import__("time").time()
        fmt = args[1].value if len(args) > 1 and isinstance(args[1], HString) else "%Y-%m-%d %H:%M:%S"
        dt = datetime.fromtimestamp(timestamp)
        return h_string(dt.strftime(fmt))

    time_env.define("format", HNativeFn("format", 2, _format_fn))

    # ------------------------------------------------------------------
    # JSON Module
    # ------------------------------------------------------------------

    json_env = Environment()
    json_env.define("parse", HNativeFn("parse", 1, lambda args, _: _json_to_hvalue(pyjson.loads(args[0].value if args and isinstance(args[0], HString) else "{}"))))
    json_env.define("stringify", HNativeFn("stringify", 1, lambda args, _: h_string(pyjson.dumps(_hvalue_to_json(args[0]), indent=2))))

    # ------------------------------------------------------------------
    # File Module (simulated in-memory)
    # ------------------------------------------------------------------

    file_store: Dict[str, str] = {}

    file_env = Environment()
    file_env.define("read", HNativeFn("read", 1, lambda args, _: h_string(file_store.get(args[0].value if args and isinstance(args[0], HString) else "", ""))))
    file_env.define("write", HNativeFn("write", 2, lambda args, _: file_store.update({(args[0].value if args and isinstance(args[0], HString) else ""): (args[1].value if len(args) > 1 and isinstance(args[1], HString) else str(args[1] if len(args) > 1 else ""))}) or h_none()))
    file_env.define("append", HNativeFn("append", 2, lambda args, _: file_store.update({(args[0].value if args and isinstance(args[0], HString) else ""): file_store.get(args[0].value if args and isinstance(args[0], HString) else "", "") + (args[1].value if len(args) > 1 and isinstance(args[1], HString) else str(args[1] if len(args) > 1 else ""))}) or h_none()))
    file_env.define("exists", HNativeFn("exists", 1, lambda args, _: h_bool((args[0].value if args and isinstance(args[0], HString) else "") in file_store)))
    file_env.define("delete", HNativeFn("delete", 1, lambda args, _: file_store.pop(args[0].value if args and isinstance(args[0], HString) else "", None) or h_none()))

    # ------------------------------------------------------------------
    # Register modules
    # ------------------------------------------------------------------

    env.define("Math", HModule("Math", math_env))
    env.define("Time", HModule("Time", time_env))
    env.define("JSON", HModule("JSON", json_env))
    env.define("File", HModule("File", file_env))

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------

    def _assert_fn(args, _):
        condition = args[0]
        message = args[1].value if len(args) > 1 and isinstance(args[1], HString) else "Assertion failed"
        truthy = is_truthy(condition)
        if not truthy:
            raise RuntimeError(message)
        return h_none()

    env.define("assert", HNativeFn("assert", 2, _assert_fn))

    return env


def is_truthy(value: HValue) -> bool:
    """Check if a value is truthy."""
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
