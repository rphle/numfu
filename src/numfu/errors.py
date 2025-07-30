import re
from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.theme import Theme

console = Console(theme=Theme({"blue": "#39bae5", "red": "#ef7177"}))


class Error:
    def __init__(
        self, message, file: str | Path = "", loc=("?", "?"), preview="", name=None
    ):
        console.print(
            f"[reset][at [blue]<{file or 'unknown'}>[/blue]:{loc[0]}:{loc[1]}]"
        )
        if preview:
            console.print(preview)
        console.print(
            f"[bold blue]{name or self.__class__.__name__}[/blue bold]: [blue]{message}[/blue]"
        )


class SyntaxError(Error):
    pass


class ValueError(Error):
    pass


class TypeError(Error):
    pass


class NameError(Error):
    pass


class LarkError(SyntaxError):
    tokens = {
        "RPAR": ")",
        "LPAR": "(",
        "COMMA": ",",
        "RSQB": "]",
        "LSQB": "[",
        "THEN": "then",
        "ELSE": "else",
    }

    def __init__(self, message: str, code: str = "", file: str | Path = ""):
        self.message = message
        self.code = code

        token = " "
        unexpected = True
        if (
            m1 := re.search(
                r"Unexpected token Token\('[^']*', '[^']*'\) at line (\d+), column (\d+)\.\nExpected one of:",
                message,
            )
        ) and (m2 := re.findall(r"\s\* (\w+)", message)):
            line, col = int(m1.group(1)), int(m1.group(2)) + 1
            try:
                expected = [f"'[bold]{self.tokens[token]}[/bold]'" for token in m2]
                message = f"Expected {'one of ' if len(expected) > 1 else ''}{', '.join(expected)}"
                unexpected = False
            except KeyError:
                pass

        if (
            m := re.search(
                r"No terminal matches '(.+)' in the current parser context, at line (\d+) col (\d+)",
                message,
            )
            or re.search(
                r"Unexpected token Token\('.+', '(.+)'\) at line (\d+), column (\d+)",
                message,
            )
        ) and unexpected:
            token, line, col = m.group(1), int(m.group(2)), int(m.group(3))
            message = f"Unexpected token '{token}'"
        else:
            super().__init__(message, file=file)
            return

        preview = ""

        if code and 0 < line <= len(code.splitlines()):
            src = escape(code.splitlines()[line - 1])
            start = max(0, col - 30)
            end = min(len(src), col + 30)

            highlighted = (
                f"{src[start:col-1]}"
                f"[red]{src[col-1:col-1+len(token)]}[/red]"
                f"{src[col-1+len(token):end]}"
            )
            prefix = "..." if start > 0 else ""
            suffix = "..." if end < len(src) else ""

            preview = (
                f"    {prefix}[reset]{highlighted}{suffix}\n"
                f"    {' ' * (col - 1 - start + len(prefix))}[red bold]{'^' * len(token)}[/bold red]"
            )

        super().__init__(
            message,
            file=file,
            preview=preview,
            name="SyntaxError",
            loc=(line, col),
        )
