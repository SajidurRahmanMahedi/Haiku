#!/usr/bin/env python3
"""
Haiku CLI
=========
Command-line interface for the Haiku programming language.
This module is the single source of truth for CLI logic, shared by:
  - python main.py          (root script)
  - python -m haiku         (package entry via haiku/__main__.py)

Usage:
    python main.py                    # Start interactive REPL
    python main.py script.hku         # Run a Haiku file
    python main.py -c "println(1+2)"  # Run code from string
    python main.py --help             # Show help
"""

import sys
import os
from .lexer import Lexer, LexerError
from .parser import Parser, ParseError
from .interpreter import Interpreter, HaikuRuntimeError
from .stdlib import create_global_env

ver = float(1.0)


def run_file(path: str):
    """Execute a Haiku source file."""
    if not os.path.exists(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    result = _run_source(source)
    if result["error"]:
        print(result["error"], file=sys.stderr)
        sys.exit(1)
    if result["output"]:
        print(result["output"], end="")


def run_repl():
    """Start an interactive Read-Eval-Print Loop."""
    print("=" * 50)
    print(f"  Haiku Programming Language v{ver}")
    print("  Type 'exit' or press Ctrl+C to quit")
    print("=" * 50)

    interpreter = Interpreter()
    globals_env = create_global_env(interpreter)
    interpreter.globals = globals_env
    interpreter.environment = globals_env

    while True:
        try:
            line = input("haiku> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        stripped = line.rstrip()
        if not stripped:
            continue
        if stripped == "exit":
            print("Goodbye!")
            break

        try:
            lexer = Lexer(line)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            interpreter.clear_output()
            interpreter.interpret(ast)
            output = interpreter.get_output()
            if output:
                # Strip trailing whitespace but preserve newlines
                output = output.rstrip()
                print(output, end="")
                # Add newline if output doesn't end with one
                if not output.endswith("\n"):
                    print()
        except LexerError as e:
            print(f"LexerError: {e}")
        except ParseError as e:
            print(f"ParseError: {e}")
        except HaikuRuntimeError as e:
            print(e.format())
        except Exception as e:
            print(f"Error: {e}")


def run_string(source: str):
    """Execute Haiku code from a string."""
    result = _run_source(source)
    if result["error"]:
        print(result["error"], file=sys.stderr)
        sys.exit(1)
    if result["output"]:
        print(result["output"], end="")


def _run_source(source: str) -> dict:
    """Internal helper to run source and return output/error."""
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        globals_env = create_global_env(interpreter)
        interpreter.globals = globals_env
        interpreter.environment = globals_env
        # Set up input provider for non-interactive execution
        interpreter.set_input_provider(lambda: input())
        # Override write methods to print immediately instead of buffering
        interpreter.write = lambda text: print(text, end="", flush=True)
        interpreter.writeln = lambda text: print(text, end="\n", flush=True)
        interpreter.interpret(ast)
        return {"output": "", "error": None}
    except LexerError as e:
        return {"output": "", "error": f"LexerError: {e}"}
    except ParseError as e:
        return {"output": "", "error": f"ParseError: {e}"}
    except HaikuRuntimeError as e:
        return {"output": "", "error": e.format()}
    except Exception as e:
        return {"output": "", "error": f"Error: {e}"}


def print_help():
    print("""
Haiku Programming Language - CLI Help
=====================================

Usage:
    python main.py [options] [file]

Options:
    -c, --code <code>    Run Haiku code from string
    -h, --help           Show this help message
    -v, --version        Show version info

Examples:
    python main.py                    # Start REPL
    python main.py script.hku         # Run file
    python main.py -c "println(42)"   # Run inline code
    python -m haiku                   # Start REPL (package mode)
    python -m haiku script.hku        # Run file (package mode)
""")


def main():
    args = sys.argv[1:]

    if not args:
        run_repl()
        return

    if args[0] in ("-h", "--help"):
        print_help()
        return

    if args[0] in ("-v", "--version"):
        print(f"Haiku {ver}")
        return

    if args[0] in ("-c", "--code"):
        if len(args) < 2:
            print("Error: -c requires code string", file=sys.stderr)
            sys.exit(1)
        run_string(args[1])
        return

    # Assume file path
    run_file(args[0])
