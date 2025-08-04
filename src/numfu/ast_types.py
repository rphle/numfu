"""
Defines all the AST node types used to represent NumFu programs.

The AST is built by the parser and consumed by the interpreter to execute
NumFu programs. All nodes inherit from the base Expr class and include
position information for error reporting.
"""

from dataclasses import dataclass, field

from .errors import Pos

DEFAULT_POS = field(default_factory=Pos, repr=False)


@dataclass
class Expr:
    pass


@dataclass
class PrintOutput(Expr):
    expr: Expr
    end: str = ""
    printed: bool = False


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

    def __eq__(self, other):
        if isinstance(other, Number):
            return self.value == other.value
        else:
            return False


@dataclass
class String(Expr):
    value: str
    pos: Pos = DEFAULT_POS

    def __repr__(self):
        return f'"{self.value}"'

    def __bool__(self):
        return bool(self.value)


@dataclass
class Bool(Expr):
    value: bool
    pos: Pos = DEFAULT_POS

    def __repr__(self):
        return "true" if self.value else "false"

    def __bool__(self):
        return self.value


@dataclass
class List(Expr):
    """
    Args:
        elements: List of expressions that make up the list
        curry: Environment captured for lazy evaluation of elements
    """

    elements: list[Expr]
    pos: Pos = DEFAULT_POS
    curry: dict[str, Expr] = field(default_factory=lambda: {}, repr=False)

    def __repr__(self):
        return f"[{', '.join(map(str, self.elements))}]"

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, index: int):
        return self.elements[index]

    def __bool__(self):
        return bool(self.elements)

    def __iter__(self):
        return iter(self.elements)

    def __eq__(self, other):
        if isinstance(other, List):
            return self.elements == other.elements
        else:
            return False


@dataclass
class Spread(Expr):
    expr: Expr
    pos: Pos = DEFAULT_POS


@dataclass
class Import(Expr):
    name: str


@dataclass
class Lambda(Expr):
    """
    Lambda function/closure.

    Args:
        arg_names: Parameter names, may include rest parameter prefixed with "..."
        body: The function body expression
        name: Optional function name
        curry: Captured environment for lazy evaluation
        tree: Serialized parse tree for code reconstruction
    """

    arg_names: list[str]
    body: Expr
    pos: Pos = DEFAULT_POS
    name: str | None = field(default_factory=lambda: None, repr=False)
    curry: dict[str, Expr] = field(default_factory=lambda: {}, repr=False)
    tree: bytes = field(default_factory=lambda: b"", repr=False)

    def __repr__(self):
        fields = [f"arg_names={self.arg_names!r}", f"body={self.body!r}"]
        if self.name is not None:
            fields.insert(0, f"name={self.name!r}")
        return f"Lambda({', '.join(fields)})"

    def __eq__(self, other):
        if not isinstance(other, Lambda):
            return False
        return (
            self.arg_names == other.arg_names
            and self.body == other.body
            and self.name == other.name
            and self.curry == other.curry
        )


@dataclass
class Constant(Expr):
    name: str
    value: Expr
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


@dataclass
class Index(Expr):
    target: Expr
    index: Expr
    pos: Pos = DEFAULT_POS


@dataclass
class Assertion(Expr):
    test: Expr
    pos: Pos = DEFAULT_POS
