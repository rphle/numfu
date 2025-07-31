from pathlib import Path
from typing import Callable

import rich
import rich.pretty
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.styles import Style

from .parser import Expr, Parser


class REPL:
    def __init__(
        self,
        imports: list[str] = ["builtins"],
        history_path: Path | str = Path.home() / ".numfu_history",
        max_depth=10,
        indent=2,
        curry=False,
        fatal=False,
    ):
        self.history_path = Path(history_path)
        self.max_depth = max_depth
        self.indent = indent
        self.curry = curry
        self.fatal = fatal
        self.parser = Parser(fatal=fatal, imports=imports)

    def print_ast(
        self,
        code="",
        tree=None,
        file_name: str | Path = "REPL",
        actually_print=True,
    ) -> tuple[Expr | list[Expr] | None, rich.pretty.Pretty | None]:
        if tree is None:
            tree = self.parser.parse(code, file=file_name, curry=self.curry)
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
