"""
Lark-based parser and AST generator for NumFu
"""

import importlib.resources
import pickle
import re
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from lark import Lark, Token, Transformer, Tree, v_args

from .errors import LarkError, Pos

OPERATORS = [
    "+",
    "-",
    "*",
    "/",
    "^",
    "%",
    "<",
    ">",
    "<=",
    ">=",
    "==",
    "!=",
    "&&",
    "||",
]

DEFAULT_POS = field(default_factory=Pos, repr=False)


def _tokpos(token: Token):
    return Pos(token.start_pos, token.end_pos)


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


grammar = importlib.resources.read_text("numfu", "grammar/numfu.lark")


@v_args(inline=True)
class LambdaPreprocessor(Transformer):
    def lambda_def(self, *args):
        return Tree(
            "lambda_def",
            [zlib.compress(pickle.dumps(Tree("lambda_def", list(args)))).hex(), *args],
        )


@v_args(inline=True)
class AstGenerator(Transformer):
    def start(self, *exprs):
        return list(exprs)

    def bin_op(self, left, op, right):
        return Call(
            Variable(str(op), pos=_tokpos(op)),
            [left, right],
            pos=Pos(left.pos.start, right.pos.end),
        )

    def comp(self, *args):
        left, op, right = args[0], args[1], args[2]
        expr = Call(
            Variable(str(op), pos=_tokpos(op)),
            [left, right],
            pos=Pos(args[0].pos.start, args[-1].pos.end),
        )

        if len(args) > 3:
            for i in range(3, len(args), 2):
                left_of_new_link = args[i - 1]
                op = args[i]
                right_of_new_link = args[i + 1]

                next_comp = Call(
                    Variable(str(op), pos=_tokpos(op)),
                    [left_of_new_link, right_of_new_link],
                    pos=_tokpos(op),
                )

                expr = Call(
                    Variable("&&", pos=_tokpos(op)),
                    [expr, next_comp],
                    pos=Pos(args[0].pos.start, args[-1].pos.end),
                )

        return expr

    def pos(self, op, value):
        return value

    def neg(self, op, value):
        return Call(Variable(str(op), pos=_tokpos(op)), [value], pos=_tokpos(op))

    def not_op(self, op, value):
        return Call(Variable(str(op), pos=_tokpos(op)), [value], pos=_tokpos(op))

    def variable(self, name):
        return Variable(str(name), pos=_tokpos(name))

    def number(self, n):
        return Number(str(n), pos=_tokpos(n))

    def boolean(self, n):
        return Bool(str(n) == "true", pos=_tokpos(n))

    def list_literal(self, *elements):
        if not elements:
            return List([], pos=Pos(0, 0))
        return List(
            list(elements), pos=Pos(elements[0].pos.start - 1, elements[-1].pos.end + 1)
        )

    def lambda_def(self, tree, *args):
        name, params, body = (None, *args) if len(args) == 2 else args
        pos = (
            _tokpos(name)
            if name
            else (_tokpos(params.children[0]) if params.children else body.pos)
        )
        arg_names = [str(t) for t in params.children]
        return Lambda(
            arg_names,
            body,
            name=str(name) if name else None,
            pos=pos,
            tree=bytes.fromhex(tree),
        )

    def let_binding(self, lambda_params, body):
        names, values = lambda_params.children[::2], lambda_params.children[1::2]
        # (let x = 3 in x * x)
        # becomes: ((x -> x * x)[3])
        return Call(
            Lambda([str(name) for name in names], body, pos=body.pos),
            values,
            pos=_tokpos(names[0]),
        )

    def list_element(self, value):
        return value

    def spread_op(self, token, value):
        return Spread(value, pos=Pos(token.start_pos, value.pos.end))

    def pipe_chain(self, *args):
        pipes = args[-2::-2]
        chain = [
            Variable(f.value, pos=_tokpos(f)) if isinstance(f, Token) else f
            for f in args[::-2]
        ]

        def construct(i=0):
            return (
                Call(func=chain[i], args=[construct(i + 1)], pos=_tokpos(pipes[i]))
                if i < len(chain) - 1
                else chain[i]
            )

        return construct()

    def constant_def(self, name, value):
        return Constant(name, value, pos=Pos(name.start_pos - 6, name.end_pos))

    def conditional(self, test, then_body, else_body):
        return Conditional(test, then_body, else_body, pos=test.pos)

    def call(self, func, args=None):
        if args is None:
            return func
        return Call(
            func,
            args,
            pos=Pos(
                args[0].pos.start - 1,
                args[-1].pos.end + 1,
            )
            if args
            else Pos(func.pos.end, func.pos.end + 2),
        )

    def call_args(self, *args):
        return list(args)


class Parser:
    def __init__(self, fatal=True, imports: list[str] = ["builtins"]):
        self.parser = Lark(grammar, parser="lalr")
        self.lambda_preprocessor = LambdaPreprocessor()
        self.generator = AstGenerator()
        self.fatal = fatal
        self.imports = imports

    def _imports(self, code: str) -> tuple[str, list[Expr]]:
        imports = []
        for i, line in enumerate(
            [f"import {imp}" for imp in self.imports] + code.splitlines()
        ):
            if m := re.search(r"^import\s+(\w+)\s*$", line):
                imports.append(Import(m.group(1)))
            else:
                code = "\n".join(code.splitlines()[max(i - len(self.imports), 0) :])
                break
        return code, imports

    def parse(
        self, code: str, file: str | Path = "", curry: bool = False
    ) -> list[Expr] | None:
        code, imports = self._imports(code)
        try:
            parse_tree = self.parser.parse(code)
            parse_tree = self.lambda_preprocessor.transform(parse_tree)
            ast_tree = self.generator.transform(parse_tree)
            if not isinstance(ast_tree, list):
                ast_tree = [ast_tree]
            if curry:
                ast_tree = self.curry(ast_tree)

        except Exception as e:
            LarkError(str(e), code=code, file=file)
            if self.fatal:
                sys.exit(1)
            return None

        ast_tree = imports + ast_tree
        return ast_tree

    def curry(self, tree: list[Expr]) -> list[Expr]:
        def c(e):
            if isinstance(e, Lambda):
                body = c(e.body)
                for a in reversed(e.arg_names):
                    body = Lambda([a], body, tree=e.tree, pos=body.pos)
                body.name = e.name
                return body
            if isinstance(e, Call):
                if isinstance(e.func, Variable) and e.func.name in OPERATORS:
                    return e
                f = c(e.func)
                for a in map(c, e.args):
                    f = Call(f, [a], pos=f.pos)
                return f
            if isinstance(e, Conditional):
                return Conditional(c(e.test), c(e.then_body), c(e.else_body), pos=e.pos)
            return e  # Variable or Number

        return [c(e) for e in tree]
