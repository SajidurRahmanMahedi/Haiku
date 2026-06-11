"""
Haiku Programming Language
==========================
A modern, expressive programming language inspired by Python.

Quick Start:
    from python_haiku import run
    result = run('println("Hello, World!")')
    print(result.output)

Or use the CLI:
    python -m python_haiku script.hku
    python -m python_haiku          # Interactive REPL
"""

from .lexer import Lexer, LexerError
from .parser import Parser, ParseError
from .interpreter import Interpreter, RuntimeError
from .stdlib import create_global_env


def run(source: str, input_provider=None):
    """
    Execute Haiku source code.

    Args:
        source: Haiku source code string
        input_provider: Optional callable that returns input strings

    Returns:
        A SimpleNamespace with attributes: output, error, result
    """
    from types import SimpleNamespace
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        if input_provider:
            interpreter.set_input_provider(input_provider)
        globals_env = create_global_env(interpreter)
        interpreter.globals = globals_env
        interpreter.environment = globals_env
        interpreter.interpret(ast)
        return SimpleNamespace(
            output=interpreter.get_output(),
            error=None,
            result=None
        )
    except Exception as e:
        return SimpleNamespace(
            output="",
            error=str(e),
            result=None
        )


__all__ = [
    "Lexer", "Parser", "Interpreter",
    "LexerError", "ParseError", "RuntimeError",
    "run", "create_global_env"
]
