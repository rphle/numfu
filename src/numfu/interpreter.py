"""
NumFu Language Interpreter

Implements the core interpreter that evaluates NumFu ASTs.
"""

import importlib.resources
import pickle
import sys
import zlib
from copy import deepcopy
from typing import Any

import lark
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
    PrintOutput,
    Spread,
    String,
    Variable,
)
from .builtins import Builtins
from .errors import (
    ErrorMeta,
    nIndexError,
    nNameError,
    nRecursionError,
    nSyntaxError,
    nTypeError,
)
from .reconstruct import reconstruct
from .typechecks import BuiltinFunc, type_name


class Interpreter:
    """
    The main NumFu interpreter that evaluates AST nodes.

    The interpreter maintains a global environment and processes expressions
    recursively. It handles function calls, variable lookups, and built-in
    operations while tracking execution context.

    Args:
        precision: Floating point precision for calculations
        rec_depth: Maximum recursion depth
        errormeta: Error context for reporting
        _print: Whether to print output or just return it at the end
    """

    def __init__(
        self,
        precision: int = 15,
        rec_depth: int = 10000,
        errormeta: ErrorMeta = ErrorMeta(),
        _print: bool = True,
    ):
        sys.setrecursionlimit(rec_depth)
        mpmath.mp.dps = precision

        self.tree: list[Expr] = []
        self.precision = precision
        self._print = _print

        self._set_errormeta(errormeta)
        self.glob: dict[Any, Any] = {
            getattr(v, "name", name): v
            for name, v in Builtins.__dict__.items()
            if not name.startswith("__")
        }

        self.output: list[str] = []  # this list collects all prints and program outputs

    def _set_errormeta(self, errormeta: ErrorMeta):
        self.errormeta, self._errormeta = errormeta, deepcopy(errormeta)
        # internal errors must be fatal so they are catched at the end and the program does not continue execution
        self._errormeta.fatal = True

    def put(self, o: str):
        self.output.append(o)
        if self._print:
            print(o, end="")

    def exception(
        self, error, message, pos: Pos | None = None, errormeta=None, line_only=False
    ) -> None:
        error(
            message,
            pos=pos,
            errormeta=self._errormeta if errormeta is None else errormeta,
            line_only=line_only,
        )

    def _partial_lambda(self, this: Lambda, args: list, env={}):
        """Return a Lambda with given args (including _ placeholders) bound, preserving printability"""

        partial_env = env.copy()
        arg_names = [a.lstrip("...") for a in this.arg_names]
        filled_pos = []

        for i, (orig_name, name, val) in enumerate(
            zip(this.arg_names, arg_names, args)
        ):
            if not (isinstance(val, Variable) and val.name == "_"):
                if orig_name.startswith("...") and not isinstance(val, List):
                    val = List([val])
                partial_env[name] = val
                filled_pos.append(i)

        remaining_params = [
            p for i, p in enumerate(this.arg_names) if i not in filled_pos
        ]

        tree = b""
        if this.tree:
            try:
                t = pickle.loads(zlib.decompress(this.tree))
                params_idx = next(
                    i
                    for i, c in enumerate(t.children)
                    if isinstance(c, lark.Tree) and c.data == "lambda_params"
                )
                t.children[params_idx].children = [
                    c
                    for i, c in enumerate(t.children[params_idx].children)
                    if i not in filled_pos
                ]
                tree = zlib.compress(pickle.dumps(t))
            except zlib.error:
                pass

        return Lambda(
            arg_names=remaining_params,
            body=this.body,
            pos=this.pos,
            name=None,
            curry=partial_env,
            tree=tree,
        )

    def _eval_lists(self, exprs):
        r = []
        for expr in exprs:
            if isinstance(expr, List):
                elements = [self._eval(arg, env=expr.curry) for arg in expr.elements]
                for i, res in enumerate(elements):
                    if isinstance(res, (List, Lambda)):
                        elements[i] = self._eval_lists([res])[0]

                r.append(List(elements, pos=expr.pos, curry=expr.curry))  # type:ignore
            else:
                r.append(expr)
        return r

    def _variable(self, this: Variable, env: dict = {}) -> Expr | None:
        if this.name == "_":
            return env.get(this.name, this)
        try:
            return env[this.name]
        except KeyError:
            self.exception(
                nNameError,
                f"'{this.name}' is not defined in the current scope",
                pos=this.pos,
            )

    def _call(self, this: Call, env: dict = {}):
        """
        Execute a function call, handling built-in functions, user lambdas, and placeholders.

        1. Handle short-circuiting logical operators (&&, ||).
        2. Evaluate the function expression to obtain the callable object.
        3. Expand any spread (...list) arguments.
        4. Evaluate all arguments.
        5. If any arguments are placeholders (_):
           - For BuiltinFunc: return a placeholder-aware partial wrapper
           - For Lambda: return a curried Lambda via _partial_lambda
        6. Otherwise, dispatch normally
        """

        # Handle short-circuiting
        if isinstance(this.func, Variable) and this.func.name in ("&&", "||"):
            left = self._eval(this.args[0], env=env)
            if this.func.name == "&&":
                return bool(self._eval(this.args[1], env=env)) if left else False
            return True if left else bool(self._eval(this.args[1], env=env))

        func = self._eval(this.func, env=env)  # type: ignore
        args = [
            self._eval(a, env=env) for a in self._resolve_spread(this.args, env=env)
        ]
        has_placeholder = any(isinstance(a, Variable) and a.name == "_" for a in args)

        # BuiltinFunc partial application
        if has_placeholder and isinstance(func, BuiltinFunc):
            fixed = args.copy()

            def partial_func(*_args, **kwargs):
                it = iter(_args)
                filled = [
                    next(it, a) if isinstance(a, Variable) and a.name == "_" else a
                    for a in fixed
                ]
                filled.extend(it)
                if any(isinstance(a, Variable) and a.name == "_" for a in filled):
                    return BuiltinFunc(
                        func.name,
                        eval_lists=func.eval_lists,
                        help=func.help,
                        partial=True,
                    ).add(
                        [Any],
                        Any,
                        lambda *ma, **mkw: partial_func(
                            *(_args + ma), **{**kwargs, **mkw}
                        ),
                    )
                return func(
                    *filled,
                    errormeta=self._errormeta,
                    args_pos=this.pos,
                    func_pos=getattr(this.func, "pos", None),  # type: ignore
                    precision=self.precision,
                    interpreter=self if func.name == "filter" else None,
                    env=env,
                )

            return BuiltinFunc(
                func.name, eval_lists=func.eval_lists, help=func.help, partial=True
            ).add([Any], Any, partial_func)

        # Lambda partial application
        if has_placeholder and isinstance(func, Lambda):
            return self._partial_lambda(func, args=args, env=env)

        # Normal calls
        if isinstance(func, BuiltinFunc):
            if func.eval_lists:
                args = self._eval_lists(args)

            args = [a.expr if isinstance(a, PrintOutput) else a for a in args]

            r = func(
                *args,
                errormeta=self._errormeta,
                args_pos=this.pos,
                func_pos=getattr(this.func, "pos", None),  # type: ignore
                precision=self.precision,
                interpreter=self if func.name == "filter" else None,
                env=env,
            )

            if isinstance(r, mpmath.mpc):
                return r if r.imag == 0 else mpmath.nan  # type: ignore
            if isinstance(r, PrintOutput):
                return self._eval(r, env=env)
            return r

        if isinstance(func, Lambda):
            return self._lambda(func, args, call_pos=this.pos, env=env)

        self.exception(nTypeError, f"{type_name(func)} is not callable", pos=this.pos)

    def _builtinfunc(self, this: BuiltinFunc, env={}):
        return this

    def _index(self, this: Index, env: dict = {}):
        target = self._eval(this.target, env=env)
        index = self._eval(this.index, env=env)

        if isinstance(target, (List, str)):
            if not isinstance(index, mpmath.mpf):
                self.exception(
                    nTypeError,
                    f"{type_name(type(target))} index must be an integer, not '{type_name(index)}'",
                    pos=this.pos,
                )

            if index % 1 != 0:  # type: ignore
                self.exception(
                    nTypeError,
                    f"{type_name(type(target))} index must be an integer, not a floating-point number",
                    pos=this.pos,
                )

            idx = int(index)  # type: ignore
            if idx >= len(target) or idx < -len(target):
                self.exception(
                    nIndexError,
                    f"{type_name(type(target))} index out of range",
                    pos=this.pos,
                )

            if idx < 0:
                idx = len(target) + idx

            if isinstance(target, str):
                return target[idx]
            else:
                return self._eval(target[idx], env=target.curry)
        else:
            self.exception(
                nTypeError,
                f"'{type_name(target)}' object is not subscriptable",
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
                        f"Type '{type_name(lst)}' is not iterable",
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
        """
        Handle lambda function calls with currying and partial application.

        - Too few args: return partially applied function
        - Exact match: execute function body
        - Too many args: apply available args, then call result with remaining

        Args:
            this: Lambda function to call
            args: Arguments provided to the function
            call_pos: Source position of function call for errors
            env: Current evaluation environment

        Returns:
            Result of function execution or partially applied lambda
        """

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
                    return result(*remaining_args)  # type: ignore
            else:
                self.exception(
                    nTypeError,
                    f"Cannot apply {len(args) - len(arg_names)} more arguments to non-callable result",
                    pos=call_pos if call_pos else this.pos,
                )

        # handle partial application
        elif len(args) < len(arg_names):
            return self._partial_lambda(this, args=args, env=new_env)

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

    def _string(self, this: String, env: dict = {}):
        return this.value

    def _constant(self, this: Constant, env: dict = {}):
        self.exception(
            nSyntaxError,
            "Constant definitions must be placed at the top level of the module",
            this.pos,
        )

    def _bool(self, this: Bool, env: dict = {}):
        return this.value

    def _printoutput(self, this: PrintOutput, env: dict = {}):
        if this.printed:
            return this.expr
        else:
            self.put(self.get_repr([this.expr])[0] + this.end)
            return PrintOutput(
                self._eval(this.expr, env=env),  # type: ignore
                end=this.end,
                printed=True,
            )

    def _eval(self, node: Expr | BuiltinFunc, env: dict = {}):
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
        elif isinstance(node, str):
            return node
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
                        )[len(b"NFU-TREE-FILE") :]
                    )
                )
            else:
                self.tree = self.tree[i:]
                break
        self.tree = imports + self.tree

    def get_repr(self, output: list[Expr]):
        o = []
        for node in output:
            if isinstance(node, (Number, mpmath._ctx_mp._mpf)):
                o.append(
                    node.value.removesuffix(".0")
                    if isinstance(node, Number)
                    else mpmath.nstr(node, self.precision).removesuffix(".0")
                )
            elif isinstance(node, (bool, Bool)):
                o.append("true" if node else "false")
            elif isinstance(node, Lambda):
                o.append(reconstruct(node, precision=self.precision, env=self.glob))
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
                    elif isinstance(res, str):
                        elements[i] = String(res)
                    elif isinstance(res, (List, Lambda)):
                        elements[i] = self.get_repr([res])[0]
                o.append(repr(List(elements)))  # type:ignore
            elif node is not None:
                o.append(str(node))
        return o

    def run(self, tree: list[Expr], errormeta: ErrorMeta | None = None):
        self.tree = tree
        if errormeta is not None:
            self._set_errormeta(errormeta)
        self.resolve_imports()

        pos = None
        try:
            for node in self.tree:
                pos = node.pos  # type:ignore
                if isinstance(node, Lambda):
                    if node.name:
                        self.glob[node.name] = node
                elif isinstance(node, Constant):
                    self.glob[node.name] = self._eval(node.value, self.glob)
                else:
                    o = self._eval(node, self.glob)
                    if o is not None and not isinstance(o, PrintOutput):
                        self.put(self.get_repr([o])[0] + "\n")  # type:ignore

            if self.output and not self.output[-1].endswith("\n"):
                self.put("\n")

        except SystemExit:
            if self.errormeta.fatal:
                sys.exit(1)

        except RecursionError:
            self.exception(
                nRecursionError,
                "maximum recursion depth exceeded",
                pos=Pos(pos.start, None) if pos else None,
                errormeta=self.errormeta,
                line_only=True,
            )

        return self.output
