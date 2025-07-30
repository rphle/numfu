"""
Lark-based parser and AST generator for NumFu
"""

import importlib.resources
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from lark import Lark, Token, Transformer, v_args

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


def _2tokpos(token1: Token, token2: Token):
    return Pos(token1.start_pos, token2.end_pos)


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


@dataclass
class Bool(Expr):
    value: bool
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

    def lambda_def(self, *args):
        name, params, body = (None, *args) if len(args) == 2 else args
        pos = (
            _tokpos(name)
            if name
            else (_tokpos(params.children[0]) if params.children else body.pos)
        )
        arg_names = [str(t) for t in params.children]
        return Lambda(arg_names, body, name=str(name) if name else None, pos=pos)

    def let_binding(self, lambda_params, body):
        names, values = lambda_params.children[::2], lambda_params.children[1::2]
        # (let x = 3 in x * x)
        # becomes: ((x -> x * x)[3])
        return Call(
            Lambda([str(name) for name in names], body, pos=body.pos),
            values,
            pos=_tokpos(names[0]),
        )

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
            ),
        )

    def call_args(self, *args):
        return list(args)


class Parser:
    def __init__(self, fatal=True, imports: list[str] = ["builtins"]):
        self.parser = Lark(grammar, parser="lalr")
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

    def clean_ast(self, tree: list[Expr]) -> list[Expr]:
        def clean(e):
            for attr in ("pos", "curry"):
                try:
                    delattr(e, attr)
                except AttributeError:
                    pass
            if isinstance(e, Lambda):
                if e.name is None:
                    del e.name
                e.body = clean(e.body)
            elif isinstance(e, Call):
                e.func = clean(e.func)
                e.args = [clean(a) for a in e.args]
            elif isinstance(e, Conditional):
                e.test = clean(e.test)
                e.then_body = clean(e.then_body)
                e.else_body = clean(e.else_body)
            return e

        return [clean(e) for e in tree]

    def curry(self, tree: list[Expr]) -> list[Expr]:
        def c(e):
            if isinstance(e, Lambda):
                body = c(e.body)
                for a in reversed(e.arg_names):
                    body = Lambda([a], body, pos=body.pos)
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
