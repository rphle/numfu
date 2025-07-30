import importlib.resources
import operator
import pickle
import sys
from pathlib import Path
from typing import Any, Callable

import mpmath

from .errors import NameError, TypeError
from .errors import ValueError as nValueError
from .parser import Call, Conditional, Expr, Import, Lambda, Number, Variable

sys.setrecursionlimit(100000)


class Builtins:
    def __init__(self, tree: list[Expr]):
        self.env: dict[str, Expr] = {
            node.name: node for node in tree if isinstance(node, Lambda) and node.name
        }

        self.funcs = {
            "+": mpmath.fadd,
            "-": lambda a, b=None: mpmath.fsub(0, a)
            if b is None
            else mpmath.fsub(a, b),
            "*": mpmath.fmul,
            "/": mpmath.fdiv,
            "^": mpmath.power,
            "%": mpmath.fmod,
            "&&": lambda a, b: mpmath.mpf(bool(a) and bool(b)),
            "||": lambda a, b: mpmath.mpf(bool(a) or bool(b)),
            "!": lambda a: mpmath.mpf(not bool(a)),
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
            **{
                name: getattr(mpmath, name)
                for name in [
                    "sin",
                    "cos",
                    "tan",
                    "sinh",
                    "cosh",
                    "tanh",
                    "asin",
                    "acos",
                    "atan",
                    "atan2",
                    "asinh",
                    "acosh",
                    "atanh",
                    "exp",
                    "log",
                    "log10",
                    "sqrt",
                    "fabs",
                    "ceil",
                    "floor",
                    "sign",
                ]
            },
        }
        self.constants = {
            "pi": mpmath.mpf(mpmath.pi),
            "e": mpmath.mpf(mpmath.e),
        }
        self.booleans = {"true": mpmath.mpf(1), "false": mpmath.mpf(0)}


class Interpreter:
    def __init__(
        self,
        tree: list[Expr],
        precision: int = 20,
        file_name: str | Path = "",
        fatal: bool = True,
    ):
        mpmath.mp.dps = precision

        self.tree: list[Expr] = tree
        self.precision = precision
        self.file_name = file_name
        self.fatal = fatal

        self.resolve_imports()
        self.builtins = Builtins(self.tree)
        self.glob: dict[Any, Any] = {
            op: self.external(op) for op in self.builtins.funcs
        }
        self.glob.update(self.builtins.booleans)
        self.glob.update(self.builtins.constants)

    def external(self, op: str):
        def extern_func(*args, env={}):
            r = self.builtins.funcs[op](*[self._eval(arg, env=env) for arg in args])
            if isinstance(r, bool):
                return mpmath.mpf(r)
            return r

        return extern_func

    def exception(self, error, message) -> None:
        error(
            message,
            self.file_name,
        )
        if self.fatal:
            sys.exit(1)

    def _variable(self, this: Variable, env: dict = {}) -> Expr | None:
        try:
            return env[this.name]
        except KeyError:
            self.exception(
                NameError, f"'{this.name}' is not defined in the current scope"
            )

    def _call(self, this: Call, env: dict = {}):
        # Handle short-circuiting
        if isinstance(this.func, Variable) and this.func.name in ("&&", "||"):
            op = this.func.name
            if len(this.args) != 2:
                self.exception(
                    nValueError,
                    f"Operator '{op}' requires 2 arguments, but got {len(this.args)}",
                )

            left = self._eval(this.args[0], env=env)

            if (op == "&&" and not bool(left)) or (op == "||" and bool(left)):
                return left

            return self._eval(this.args[1], env=env)

        func = self._eval(this.func, env=env)
        args = [self._eval(arg, env=env) for arg in this.args]

        if isinstance(func, Callable):
            return func(*args, env=env)
        elif not isinstance(func, Lambda):
            self.exception(TypeError, f"{type(func).__name__} is not callable")
        else:
            return self._lambda(func, args, env=env)

    def _conditional(self, this: Conditional, env: dict = {}):
        condition = self._eval(this.test, env=env)
        return self._eval(this.then_body if condition else this.else_body, env=env)

    def _lambda(self, this: Lambda, args: list = [], env: dict = {}):
        new_env = env.copy()

        if this.name:
            new_env[this.name] = this

        new_env.update(this.curry)

        if len(args) != len(this.arg_names):
            self.exception(
                nValueError,
                f"Wrong number of arguments for '{this.name if this.name else ', '.join(this.arg_names) + '-> ...'}': {len(args)} != {len(this.arg_names)}",
            )
            sys.exit(1)

        new_env.update(zip(this.arg_names, args))

        return self._eval(this.body, env=new_env)

    def _number(self, this: Number, env: dict = {}):
        return mpmath.mpf(this.value)

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
        elif isinstance(node, (float, int, str, mpmath.mpf)):
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

    def run(self):
        r = []
        for node in self.tree:
            if isinstance(node, Lambda):
                if node.name:
                    self.glob[node.name] = node
            else:
                r.append(self._eval(node, self.glob))
        return r
