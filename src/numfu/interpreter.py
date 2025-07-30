import importlib.resources
import pickle
import sys
from pathlib import Path
from typing import Any, Callable

import mpmath

from .builtins import Builtins, Operators
from .errors import nNameError, nSyntaxError, nTypeError, nValueError
from .parser import (
    Bool,
    Call,
    Conditional,
    Constant,
    Expr,
    Import,
    Lambda,
    Number,
    Pos,
    Variable,
)

sys.setrecursionlimit(100000)


class Interpreter:
    def __init__(
        self,
        tree: list[Expr],
        precision: int = 20,
        file_name: str | Path = "",
        repr=True,
        fatal: bool = True,
        code: str = "",
    ):
        mpmath.mp.dps = precision

        self.tree: list[Expr] = tree
        self.precision = precision
        self.file_name = file_name
        self.repr = repr
        self.fatal = fatal
        self.code = code

        self.resolve_imports()
        self.glob: dict[Any, Any] = {
            Operators.get(name, name): v
            for name, v in Builtins.__dict__.items()
            if not name.startswith("__")
        }

    def exception(self, error, message, pos: Pos = Pos(-1, -1)) -> None:
        error(message, self.file_name, pos=pos, code=self.code)
        sys.exit(1)

    def _variable(self, this: Variable, env: dict = {}) -> Expr | None:
        try:
            return env[this.name]
        except KeyError:
            self.exception(
                nNameError,
                f"'{this.name}' is not defined in the current scope",
                pos=this.pos,
            )

    def _call(self, this: Call, env: dict = {}):
        # Handle short-circuiting
        if isinstance(this.func, Variable) and this.func.name in ("&&", "||"):
            op = this.func.name
            if op == "&&":
                return (
                    bool(self._eval(this.args[1], env=env))
                    if self._eval(this.args[0], env=env)
                    else False
                )
            elif op == "||":
                return (
                    True
                    if self._eval(this.args[0], env=env)
                    else bool(self._eval(this.args[1], env=env))
                )

        func = self._eval(this.func, env=env)
        args = [self._eval(arg, env=env) for arg in this.args]

        if isinstance(func, Callable):
            return func(*[self._eval(arg, env=env) for arg in args])
        elif not isinstance(func, Lambda):
            self.exception(
                nTypeError, f"{type(func).__name__} is not callable", pos=this.pos
            )
        else:
            if len(args) != len(func.arg_names):
                self.exception(
                    nValueError,
                    f"Wrong number of arguments for '{func.name if func.name else ', '.join(func.arg_names) + '-> ...'}': {len(args)} != {len(func.arg_names)}",
                    pos=this.pos,
                )

            return self._lambda(func, args, env=env)

    def _conditional(self, this: Conditional, env: dict = {}):
        condition = self._eval(this.test, env=env)
        return self._eval(this.then_body if condition else this.else_body, env=env)

    def _lambda(self, this: Lambda, args: list = [], env: dict = {}):
        new_env = env.copy()

        if this.name:
            new_env[this.name] = this

        new_env.update(this.curry)

        new_env.update(zip(this.arg_names, args))

        return self._eval(this.body, env=new_env)

    def _number(self, this: Number, env: dict = {}):
        return mpmath.mpf(this.value)

    def _constant(self, this: Constant, env: dict = {}):
        self.exception(
            nSyntaxError,
            "Constant definitions must be placed at the top level of the module",
            this.pos,
        )

    def _bool(self, this: Bool, env: dict = {}):
        return this.value

    def _eval(self, node: Expr, env: dict = {}):
        if isinstance(node, Lambda):
            lambda_copy = Lambda(
                arg_names=node.arg_names,
                body=node.body,
                name=node.name,
                curry=env.copy(),
                pos=node.pos,
            )
            return lambda_copy
        elif isinstance(node, (float, int, mpmath.mpf)):
            return mpmath.mpf(node)
        elif node is None:
            return mpmath.mpf(0)
        try:
            return getattr(self, "_" + type(node).__name__.lower())(node, env=env)
        except AttributeError as e:
            raise e

    def resolve_imports(self):
        imports = []
        for i, node in enumerate(self.tree):
            if isinstance(node, Import):
                imports = [
                    *imports,
                    *(
                        pickle.loads(
                            importlib.resources.read_binary(
                                "numfu", f"stdlib/{node.name}.nfut"
                            )
                        )
                    ),
                ]
            else:
                self.tree = self.tree[i:]
                break
        self.tree = imports + self.tree

    def get_repr(self, output: list[Number | Bool]):
        o = []
        for node in output:
            if isinstance(node, Number):
                o.append(node.value.removesuffix(".0"))
            elif isinstance(node, Bool):
                o.append("true" if node.value else "false")
            else:
                o.append(str(node))
        return o

    def run(self):
        try:
            r = []
            for node in self.tree:
                if isinstance(node, Lambda):
                    if node.name:
                        self.glob[node.name] = node
                elif isinstance(node, Constant):
                    self.glob[node.name] = node.value
                else:
                    r.append(self._eval(node, self.glob))

            for i, res in enumerate(r):
                if isinstance(res, mpmath.mpf):
                    r[i] = Number(mpmath.nstr(res, self.precision))
                elif isinstance(res, bool):
                    r[i] = Bool(res)

            if self.repr:
                return self.get_repr(r)

            return r
        except SystemExit:
            if self.fatal:
                sys.exit(1)
            return []
