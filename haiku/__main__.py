"""
Entry point for `python -m haiku`.

Allows running the Haiku interpreter as a package:
    python -m haiku                 # Start REPL
    python -m haiku script.hku     # Run a file
    python -m haiku -c "..."       # Run inline code
"""
from .cli import main

if __name__ == "__main__":
    main()
