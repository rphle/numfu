import importlib.resources
import pickle
import sys
import zlib
from pathlib import Path
from typing import Any

import lark
import lark.reconstruct
import mpmath

from .ast_types import (
    Bool,
    Call,
    Conditional,
    Constant,
    Expr,
    Import,
    Index,
    Lambda,
    List,
    Number,
    Pos,
    Spread,
    Variable,
)
from .builtins import Builtins
from .errors import nIndexError, nNameError, nSyntaxError, nTypeError
from .typechecks import BuiltinFunc, type_name


class Interpreter:
    def __init__(
        self,
        tree: list[Expr],
        precision: int = 20,
        rec_depth: int = 10000,
        file_name: str | Path = "",
        repr=True,
        fatal: bool = True,
        code: str = "",
    ):
        sys.setrecursionlimit(rec_depth)
        mpmath.mp.dps = precision

        self.tree: list[Expr] = tree
        self.precision = precision
        self.file_name = file_name
        self.repr = repr
        self.fatal = fatal
        self.code = code

        self.resolve_imports()
        self.glob: dict[Any, Any] = {
            v.name: v
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
        resolved_args = self._resolve_spread(this.args, env=env)
        args = [self._eval(arg, env=env) for arg in resolved_args]

        if isinstance(func, BuiltinFunc):
            return func(*args)
        elif isinstance(func, Lambda):
            return self._lambda(func, args, call_pos=this.pos, env=env)
        else:
            self.exception(
                nTypeError,
                f"{type_name(type(func).__name__)} is not callable",
                pos=this.pos,
            )

    def _index(self, this: Index, env: dict = {}):
        target = self._eval(this.target, env=env)
        index = self._eval(this.index, env=env)

        if isinstance(target, List):
            if not isinstance(index, mpmath.mpf):
                self.exception(
                    nTypeError,
                    f"List index must be an integer, not '{type_name(type(index).__name__)}'",
                    pos=this.pos,
                )

            if index % 1 != 0:  # type: ignore
                self.exception(
                    nTypeError,
                    "List index must be an integer, not a floating-point number",
                    pos=this.pos,
                )

            idx = int(index)  # type: ignore
            if idx >= len(target.elements) or idx < -len(target.elements):
                self.exception(
                    nIndexError,
                    "List index out of range",
                    pos=this.pos,
                )

            if idx < 0:
                idx = len(target.elements) + idx

            return self._eval(target.elements[idx], env=target.curry)  # type: ignore
        else:
            self.exception(
                nTypeError,
                f"'{type_name(type(target).__name__)}' object is not subscriptable",
                pos=this.pos,
            )

    def _resolve_spread(self, _elements, env={}):
        elements = []
        for i, element in enumerate(_elements):
            if isinstance(element, Spread):
                lst = self._eval(element.expr, env=env)
                if not isinstance(lst, List):
                    self.exception(
                        nTypeError,
                        f"Type '{type_name(type(lst).__name__)}' is not iterable",
                        pos=element.pos,
                    )
                else:
                    elements.extend(lst.elements)
            else:
                elements.append(element)
        return elements

    def _list(self, this: List, env: dict = {}):
        this.curry = env.copy()
        this.elements = self._resolve_spread(this.elements, env=env)
        return this

    def _spread(self, this: Spread, env: dict = {}):
        return this

    def _conditional(self, this: Conditional, env: dict = {}):
        condition = self._eval(this.test, env=env)
        return self._eval(this.then_body if condition else this.else_body, env=env)

    def _lambda(
        self, this: Lambda, args: list = [], call_pos: Pos | None = None, env: dict = {}
    ):
        new_env = env.copy()

        if this.name:
            new_env[this.name] = this

        # merge curried environment
        new_env.update(this.curry)

        catch_rest = any(arg.startswith("...") for arg in this.arg_names)
        arg_names = [arg.lstrip("...") for arg in this.arg_names.copy()]

        # more arguments than parameters
        if len(args) > len(arg_names) and not catch_rest:
            # apply all parameters and call the result with remaining args
            filled_env = new_env.copy()
            filled_env.update(zip(arg_names, args[: len(arg_names)]))
            result = self._eval(this.body, env=filled_env)

            # if result is callable, call it with remaining args
            if isinstance(result, (Lambda, BuiltinFunc)) or hasattr(result, "__call__"):
                remaining_args = args[len(arg_names) :]
                if isinstance(result, Lambda):
                    return self._lambda(
                        result, remaining_args, call_pos=call_pos, env=env
                    )
                else:
                    # builtin function
                    return result(*remaining_args)
            else:
                self.exception(
                    nTypeError,
                    f"Cannot apply {len(args) - len(arg_names)} more arguments to non-callable result",
                    pos=call_pos if call_pos else this.pos,
                )

        # handle partial application
        elif len(args) < len(arg_names) and not catch_rest:
            # create a new lambda with the remaining parameters
            remaining_params = arg_names[len(args) :]
            partial_env = new_env.copy()
            partial_env.update(zip(arg_names[: len(args)], args))

            # create new tree for later reconstruction (delete consumed args)
            tree = b""
            if this.tree:
                try:
                    tree = pickle.loads(zlib.decompress(this.tree))
                    params_i = next(
                        i
                        for i, c in enumerate(
                            pickle.loads(zlib.decompress(this.tree)).children
                        )
                        if isinstance(c, lark.Tree) and c.data == "lambda_params"
                    )
                    del tree.children[params_i].children[0]
                    tree = zlib.compress(pickle.dumps(tree))
                except zlib.error:
                    tree = b""

            return Lambda(
                arg_names=remaining_params,
                body=this.body,
                pos=this.pos,
                name=None,
                curry=partial_env,
                tree=tree,
            )

        # exact match: apply all arguments
        else:
            if catch_rest:
                new_env.update(zip(arg_names[:-1], args[: len(arg_names[:-1])]))
                new_env[arg_names[-1]] = List(args[len(arg_names[:-1]) :])
            else:
                new_env.update(zip(arg_names, args))
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
            # Don't re-evaluate lambdas that already have a curry environment
            if hasattr(node, "curry") and node.curry:
                curry = node.curry.copy() | env
            else:
                curry = env.copy()

            lambda_copy = Lambda(
                arg_names=node.arg_names,
                body=node.body,
                name=node.name,
                curry=curry,
                tree=node.tree,
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
                imports.extend(
                    pickle.loads(
                        importlib.resources.read_binary(
                            "numfu", f"stdlib/{node.name}.nfut"
                        )
                    )
                )
            else:
                self.tree = self.tree[i:]
                break
        self.tree = imports + self.tree

    def reconstruct(self, node: Lambda):
        if not node.tree:
            return None
        grammar = importlib.resources.read_text("numfu", "grammar/numfu.lark")
        reconstructor = lark.reconstruct.Reconstructor(
            lark.Lark(grammar, parser="lalr")
        )
        tree = pickle.loads(zlib.decompress(node.tree))
        env = {k: v for k, v in node.curry.items() if k not in self.glob}

        class Resolver(lark.Transformer):
            def variable(self, name):
                value = env.get(name[0].value, name[0])
                if isinstance(value, mpmath.mpf):
                    value = lark.Tree(
                        "number",
                        [lark.Token("NUMBER", mpmath.nstr(value).removesuffix(".0"))],  # type: ignore
                    )
                elif isinstance(value, Lambda):
                    value = pickle.loads(zlib.decompress(value.tree))
                else:
                    value = lark.Tree("variable", [value])  # type: ignore

                return value

        tree = Resolver().transform(tree)
        return reconstructor.reconstruct(tree)

    def get_repr(self, output: list[Number | Bool | List | Lambda]):
        o = []
        for node in output:
            if isinstance(node, Number):
                o.append(node.value.removesuffix(".0"))
            elif isinstance(node, Bool):
                o.append("true" if node.value else "false")
            elif isinstance(node, Lambda):
                o.append(self.reconstruct(node))
            elif isinstance(node, List):
                elements = [
                    self._eval(arg, env=node.curry)  # type: ignore
                    for arg in node.elements
                ]
                for i, res in enumerate(elements):
                    if isinstance(res, mpmath.mpf):
                        elements[i] = Number(mpmath.nstr(res, self.precision))
                    elif isinstance(res, bool):
                        elements[i] = Bool(res)
                    elif isinstance(res, (List, Lambda)):
                        elements[i] = self.get_repr([res])[0]
                o.append(List(elements))  # type:ignore
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
