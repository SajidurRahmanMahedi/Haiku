#!/usr/bin/env python3
"""
Haiku CLI - root script entry point.

This file exists so you can run:
    python main.py [args...]

All actual CLI logic lives in haiku/cli.py, which is also used by
`python -m haiku` via haiku/__main__.py.
"""
from haiku.cli import main

if __name__ == "__main__":
    main()
