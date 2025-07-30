import re
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.theme import Theme

console = Console(theme=Theme({"blue": "#39bae5", "red": "#ef7177"}))


@dataclass
class Pos:
    start: int = 0
    end: int = 1


class CPos:
    def __init__(
        self, line: int = 1, col: int = 1, end_line: int = 1, end_col: int = 2
    ):
        self.line = line
        self.col = col
        self.end_line = end_line
        self.end_col = end_col

    @classmethod
    def frompos(cls, pos: Pos, code: str):
        self = cls()
        self.line = code.count("\n", 0, pos.start) + 1
        self.col = pos.start - code.rfind("\n", 0, pos.start)
        self.end_line = code.count("\n", 0, pos.end) + 1
        self.end_col = pos.end - code.rfind("\n", 0, pos.end)
        return self

    def split(self) -> list["CPos"]:
        return [
            CPos(
                line=line,
                col=self.col if line == self.line else 1,
                end_line=line,
                end_col=-1 if line != self.end_line else self.end_col,
            )
            for line in range(self.line, self.end_line + 1)
        ]

    def __repr__(self):
        return f"CPos(line={self.line}, col={self.col}, end_line={self.end_line}, end_col={self.end_col})"


class Error:
    def __init__(
        self,
        message,
        file: str | Path = "",
        pos: Pos | CPos | None = None,
        code="",
        name=None,
    ):
        if pos is None:
            cpos = None
        elif isinstance(pos, Pos):
            cpos = CPos.frompos(pos, code)
        elif isinstance(pos, CPos):
            cpos = pos
        else:
            raise TypeError(f"Invalid position type: {type(pos)}")

        console.print(
            f"[reset][at [blue]<{file or 'unknown'}>[/blue]:{cpos.line if cpos else '?'}:{cpos.col if cpos else '?'}]"
        )
        if cpos is not None:
            if code and 0 < cpos.end_line <= len(code.splitlines()):
                for _cpos in cpos.split():
                    _cpos.end_line = (
                        _cpos.end_line if _cpos.end_line > 0 else len(code.splitlines())
                    )
                    _cpos.end_col = (
                        _cpos.end_col
                        if _cpos.end_col > 0
                        else len(code.splitlines()[_cpos.line - 1]) + 1
                    )

                    src = escape(code.splitlines()[_cpos.line - 1])
                    start = max(0, _cpos.col - 30)
                    end = min(len(src), _cpos.col + 30)

                    highlighted = (
                        f"{src[start:_cpos.col-1]}"
                        f"[red]{src[_cpos.col-1:_cpos.end_col-1]}[/red]"
                        f"{src[_cpos.end_col-1:end]}"
                    )
                    prefix = "..." if start > 0 else ""
                    suffix = "..." if end < len(src) else ""
                    console.print(
                        f"[reset][dim][{_cpos.line}][/dim]   {prefix}[reset]{highlighted}{suffix}\n"
                        f"    {' ' * (_cpos.col - start + len(prefix)+len(str(_cpos.line)))}[red bold]{'^' * (_cpos.end_col - _cpos.col)}[/bold red]"
                    )

        console.print(
            f"[bold blue]{name or self.__class__.__name__.removeprefix("n")}[/blue bold]: [blue]{message}[/blue]"
        )


class nSyntaxError(Error):
    pass


class nValueError(Error):
    pass


class nTypeError(Error):
    pass


class nNameError(Error):
    pass


class LarkError(nSyntaxError):
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

        super().__init__(
            message,
            file=file,
            code=code,
            name="SyntaxError",
            pos=CPos(line, col, line, col + len(token)),
        )
