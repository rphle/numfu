from dataclasses import dataclass, field

from .errors import Pos

DEFAULT_POS = field(default_factory=Pos, repr=False)


@dataclass
class Expr:
    pass


@dataclass
class Variable(Expr):
    name: str
    pos: Pos = DEFAULT_POS


@dataclass
class Number(Expr):
    value: str
    pos: Pos = DEFAULT_POS

    def __repr__(self):
        return self.value.removesuffix(".0")


@dataclass
class Bool(Expr):
    value: bool
    pos: Pos = DEFAULT_POS

    def __repr__(self):
        return "true" if self.value else "false"


@dataclass
class List(Expr):
    elements: list[Expr]
    pos: Pos = DEFAULT_POS
    curry: dict[str, Expr] = field(default_factory=lambda: {}, repr=False)

    def __repr__(self):
        return f"[{', '.join(map(str, self.elements))}]"


@dataclass
class Spread(Expr):
    expr: Expr
    pos: Pos = DEFAULT_POS


@dataclass
class Import(Expr):
    name: str


@dataclass
class Lambda(Expr):
    arg_names: list[str]
    body: Expr
    pos: Pos = DEFAULT_POS
    name: str | None = field(default_factory=lambda: None, repr=False)
    curry: dict[str, Expr] = field(default_factory=lambda: {}, repr=False)
    tree: bytes = field(default_factory=lambda: b"", repr=False)


@dataclass
class Constant(Expr):
    name: str
    value: str
    pos: Pos = DEFAULT_POS


@dataclass
class Conditional(Expr):
    test: Expr
    then_body: Expr
    else_body: Expr
    pos: Pos = DEFAULT_POS


@dataclass
class Call(Expr):
    func: Expr
    args: list[Expr]
    pos: Pos = DEFAULT_POS
