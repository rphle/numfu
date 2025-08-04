"""
Read-Eval-Print Loop (REPL) for NumFu

Supports both normal evaluation mode and AST inspection mode
for debugging and learning about NumFu's internal representation.
"""

from pathlib import Path
from typing import Callable

import rich
import rich.pretty
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.styles import Style

from .parser import Expr


class REPL:
    """
    Interactive REPL environment for NumFu programming.

    Provides a command-line interface for interactive NumFu programming
    with history, multi-line editing, and rich output formatting.

    Args:
        history_path: File path for persistent command history
        max_depth: Maximum depth for AST pretty-printing
        indent: Indentation size for formatted output
    """

    def __init__(
        self,
        history_path: Path | str = Path.home() / ".numfu_history",
        max_depth=10,
        indent=2,
    ):
        self.history_path = Path(history_path)
        self.max_depth = max_depth
        self.indent = indent
        self.glob = {}

    def print_ast(
        self,
        tree=None,
        actually_print=True,
    ) -> tuple[Expr | list[Expr] | None, rich.pretty.Pretty | None]:
        if tree is None:
            return (None, None)

        output = rich.pretty.Pretty(
            tree,
            indent_guides=False,
            max_depth=self.max_depth,
            indent_size=self.indent,
        )

        if actually_print:
            rich.print(output)

        return tree, output

    def start(
        self, do: Callable, intro="NumFu REPL. Type 'exit' or press Ctrl+D to exit."
    ):
        """Start a REPL."""

        session = PromptSession(
            history=FileHistory(str(self.history_path)),
            style=Style.from_dict(
                {
                    "prompt": "fg:#39bae5 bold",
                }
            ),
            color_depth=ColorDepth.TRUE_COLOR,
        )

        print(intro)

        while True:
            try:
                code = []
                code.append(session.prompt(">>> ").strip())
                while code[-1].endswith("\\"):
                    code.append(session.prompt("... ").strip())
                code = "\n".join([line.removesuffix("\\") for line in code])
            except KeyboardInterrupt:
                print("(Type 'exit' or press Ctrl+D to exit)")
                continue
            except EOFError:
                break

            if not code:
                continue
            if code.lower() == "exit":
                break

            do(code)
