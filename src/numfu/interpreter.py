"""
NumFu Language Interpreter

Implements the core interpreter that evaluates NumFu ASTs.
"""

import dataclasses
import math
import pickle
import sys
import zlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import lark
import mpmath

from .ast_types import (
    Bool,
    Call,
    Conditional,
    Constant,
    Delete,
    Export,
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
from .classes import Module, State
from .errors import (
    Error,
    nIndexError,
    nNameError,
    nRecursionError,
    nTypeError,
)
from .modules import ImportResolver
from .reconstruct import reconstruct
from .typechecks import BuiltinFunc, InfiniteOf, type_name


@dataclass
class Bounce:
    """tail-call trampoline"""

    func: Lambda
    args: list
    env: dict
    call_pos: Any


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
        iter_depth: int = -1,
        fatal: bool = True,
        _print: bool = True,
    ):
        sys.setrecursionlimit(rec_depth)
        mpmath.mp.dps = precision
        self.rec_depth = rec_depth
        self.iter_depth = iter_depth if iter_depth >= 0 else math.inf

        self.fatal = fatal
        self.precision = precision
        self._print = _print

        self.modules: dict[str, Module] = {}
        self.module_id: str

        self.builtins: dict[Any, Any] = {
            getattr(v, "name", name): v
            for name, v in Builtins.__dict__.items()
            if not name.startswith("__")
        }

        self.output: list[str] = []  # this list collects all prints and program outputs

    def put(self, o: str):
        self.output.append(o)
        if self._print:
            print(o, end="")

    def exception(
        self,
        error: type[Error],
        message: str,
        pos: Pos | None = None,
        line_only=False,
        state: State = State(),
    ) -> None:
        error(
            message,
            pos=pos,
            module=self.modules[state.module],
            line_only=line_only,
        )

    def validate_exports(self, module: Module):
        """
        Verify that export statements only export previously declared symbols.
        """
        declared = set(module.imports.keys())
        for node in module.tree:
            # Check if node is an export statement which contains a name not contained in declared
            # (I use iterators & co. way too much, I'm sorry)
            if isinstance(node, Export):
                if (
                    missing := next(
                        (name for name in node.names if name.name not in declared),
                        None,
                    )
                ) is not None:
                    nNameError(
                        f"'{missing.name}' is not defined in the current scope",
                        missing.pos,
                        self.modules[module.id],
                        fatal=self.fatal,
                    )

            elif isinstance(node, Constant):
                declared.add(node.name)

    def _merge_modules(self, modules: dict[str, Module]):
        if len(modules) == 0:
            return

        self.modules = {
            **{
                module_id: module
                for module_id, module in modules.items()
                if module_id not in self.modules
            },
            **self.modules,  # keep -1 index
        }

        this = list(self.modules.keys())[-1]
        self.modules[this].imports = (
            modules[list(modules.keys())[-1]].imports | self.modules[this].imports
        )

    @lru_cache()
    def _declared_constants(self, module_id: str, index: int):
        # find all constants declared up to a given index in the tree
        return {
            c.name: c.value
            for c in self.modules[module_id].tree
            if isinstance(c, Constant) and c.pos.index <= index  # type: ignore
        }

    def _partial_lambda(self, this: Lambda, args: list, state: State = State()):
        """Return a Lambda with given args (including _ placeholders) bound, preserving printability"""

        def is_placeholder(arg):
            return isinstance(arg, Variable) and arg.name == "_"

        partial_env = state.env.copy()
        arg_names = [a.lstrip("...") for a in this.arg_names]
        filled_pos = []

        rest_index = next(
            (i for i, name in enumerate(this.arg_names) if name.startswith("...")), None
        )

        for i, (orig_name, name) in enumerate(zip(this.arg_names, arg_names)):
            if i >= len(args):
                break

            if orig_name.startswith("..."):
                rest_args = [arg for arg in args[i:] if not is_placeholder(arg)]
                if rest_args:
                    partial_env[name] = List(rest_args)
                    filled_pos.extend(range(i, len(this.arg_names)))
                break
            elif not is_placeholder(args[i]):
                partial_env[name] = args[i]
                filled_pos.append(i)

        if rest_index is not None and len(args) > len(arg_names):
            rest_name = arg_names[rest_index]
            extra_non_placeholders = [
                arg for arg in args[len(arg_names) :] if not is_placeholder(arg)
            ]

            if extra_non_placeholders:
                existing = partial_env.get(rest_name, List([]))
                combined_elements = (
                    existing.elements if isinstance(existing, List) else []
                ) + extra_non_placeholders
                partial_env[rest_name] = List(combined_elements)

        remaining_params = [
            p
            for i, p in enumerate(this.arg_names)
            if i not in filled_pos
            and (not p.startswith("...") or p.lstrip("...") not in partial_env)
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
            curry=partial_env,
            tree=tree,
        )

    def _eval_lists(self, exprs, state: State):
        r = []
        for expr in exprs:
            if isinstance(expr, List):
                elements = [
                    self._eval(arg, state=state.edit(env=expr.curry))
                    for arg in expr.elements
                ]
                for i, res in enumerate(elements):
                    if isinstance(res, (List, Lambda)):
                        elements[i] = self._eval_lists([res], state=state)[0]

                r.append(List(elements, pos=expr.pos, curry=expr.curry))  # type:ignore
            else:
                r.append(expr)
        return r

    def _variable(self, this: Variable, state: State = State()) -> Expr | None:
        if this.name == "_":
            return state.env.get(this.name, this)

        if this.name in (env := state.env):
            return env[this.name]
        elif this.name in self._declared_constants(state.module, state.index):
            return self.modules[state.module].globals[this.name]
        elif this.name in list(self.modules[state.module].imports.keys()):
            # resolve variable which was imported from another module
            module = self.modules[self.modules[state.module].imports[this.name]]

            res = self._eval(
                self._eval(
                    dataclasses.replace(this, name=this.name.split(".")[-1]),  # type: ignore
                    state=state.edit(module=module.id),
                ),
                state=state.edit(module=module.id),
            )

            return res  # type: ignore
        elif this.name in (env := self.builtins):
            return env[this.name]

        self.exception(
            nNameError,
            f"'{this.name}' is not defined in the current scope",
            pos=this.pos,
            state=state,
        )

    def _call(self, this: Call, is_tail: bool = False, state: State = State()):
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
            left = self._eval(this.args[0], state=state)
            if this.func.name == "&&":
                return bool(self._eval(this.args[1], state=state)) if left else False
            return True if left else bool(self._eval(this.args[1], state=state))

        func = self._eval(this.func, state=state)  # type: ignore
        if isinstance(func, Lambda) and func.pos.module is not None:
            state = state.edit(module=func.pos.module)

        args = [
            self._eval(a, state=state)
            for a in self._resolve_spread(this.args, state=state)
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

                if func.eval_lists:
                    filled = self._eval_lists(filled, state=state)
                filled = [a.expr if isinstance(a, PrintOutput) else a for a in filled]

                if any(isinstance(a, Variable) and a.name == "_" for a in filled):
                    return BuiltinFunc(
                        func.name,
                        eval_lists=func.eval_lists,
                        help=func.help,
                        partial=True,
                    ).add(
                        [Any, InfiniteOf(Any)],
                        Any,
                        lambda *ma, **mkw: partial_func(
                            *(_args + ma), **{**kwargs, **mkw}
                        ),
                    )

                return func(
                    *filled,
                    module=self.modules[state.module],
                    args_pos=this.pos,
                    func_pos=getattr(this.func, "pos", None),  # type: ignore
                    precision=self.precision,
                    interpreter=self if func.name == "filter" else None,
                    state=state,
                )

            return BuiltinFunc(
                func.name, eval_lists=func.eval_lists, help=func.help, partial=True
            ).add([Any, InfiniteOf(Any)], Any, partial_func)

        # Lambda partial application
        if has_placeholder and isinstance(func, Lambda):
            return self._partial_lambda(func, args=args, state=state)

        # Normal calls
        if isinstance(func, BuiltinFunc):
            if func.eval_lists:
                args = self._eval_lists(args, state=state)

            args = [a.expr if isinstance(a, PrintOutput) else a for a in args]

            r = func(
                *args,
                module=self.modules[state.module],
                args_pos=this.pos,
                func_pos=getattr(this.func, "pos", None),  # type: ignore
                precision=self.precision,
                interpreter=self if func.name == "filter" else None,
                state=state,
            )

            if isinstance(r, mpmath.mpc):
                return r if r.imag == 0 else mpmath.nan  # type: ignore
            if isinstance(r, PrintOutput):
                return self._eval(r, state=state)
            return r

        # return a Bounce so the caller's trampoline can iterate instead of recursing.
        if isinstance(func, Lambda):
            if is_tail:
                return Bounce(func, args, state.env, this.pos)
            return self._lambda(func, args, call_pos=this.pos, state=state)

        self.exception(
            nTypeError, f"{type_name(func)} is not callable", pos=this.pos, state=state
        )

    def _builtinfunc(self, this: BuiltinFunc, state: State = State()):
        return this

    def _index(self, this: Index, state: State = State()):
        target = self._eval(this.target, state=state)
        index = self._eval(this.index, state=state)

        if isinstance(target, (List, str)):
            if not isinstance(index, mpmath.mpf):
                self.exception(
                    nTypeError,
                    f"{type_name(type(target))} index must be an integer, not '{type_name(index)}'",
                    pos=this.pos,
                    state=state,
                )

            if index % 1 != 0:  # type: ignore
                self.exception(
                    nTypeError,
                    f"{type_name(type(target))} index must be an integer, not a floating-point number",
                    pos=this.pos,
                    state=state,
                )

            idx = int(index)  # type: ignore
            if idx >= len(target) or idx < -len(target):
                self.exception(
                    nIndexError,
                    f"{type_name(type(target))} index out of range",
                    pos=this.pos,
                    state=state,
                )

            if idx < 0:
                idx = len(target) + idx

            if isinstance(target, str):
                return target[idx]
            else:
                return self._eval(target[idx], state=state.edit(env=target.curry))
        else:
            self.exception(
                nTypeError,
                f"'{type_name(target)}' object is not subscriptable",
                pos=this.pos,
                state=state,
            )

    def _resolve_spread(self, _elements, state: State = State()):
        elements = []
        for i, element in enumerate(_elements):
            if isinstance(element, Spread):
                lst = self._eval(element.expr, state=state)
                if not isinstance(lst, List):
                    if isinstance(lst, Variable) and lst.name == "_":
                        self.exception(
                            nTypeError,
                            "Cannot combine spread operator with argument placeholder",
                            pos=element.pos,
                            state=state,
                        )
                    else:
                        self.exception(
                            nTypeError,
                            f"Type '{type_name(lst)}' is not iterable",
                            pos=element.pos,
                            state=state,
                        )
                else:
                    elements.extend(lst.elements)
            else:
                elements.append(element)
        return elements

    def _list(self, this: List, state: State = State()):
        this.curry = state.env.copy()
        this.elements = self._resolve_spread(this.elements, state=state)
        return this

    def _spread(self, this: Spread, state: State = State()):
        return this

    def _conditional(
        self, this: Conditional, is_tail: bool = False, state: State = State()
    ):
        condition = self._eval(this.test, state=state)
        return self._eval(
            this.then_body if condition else this.else_body,
            is_tail=is_tail,
            state=state,
        )

    def _lambda(
        self,
        this: Lambda,
        args: list = [],
        call_pos: Pos | None = None,
        is_tail: bool = False,
        state: State = State(),
    ):
        """
        Handle lambda function calls with currying and partial application.
        Also handles tail-call Bounces.

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
        current_lambda = this
        current_args = args
        current_env = state.env

        iterations = 0
        while True:
            iterations += 1
            if iterations > self.iter_depth:
                self.exception(
                    nRecursionError,
                    "tail-call recursion limit exceeded",
                    pos=Pos(call_pos.start, None) if call_pos else None,
                    line_only=True,
                    state=state,
                )

            new_env = current_env.copy()
            new_env.update(current_lambda.curry)

            catch_rest = any(arg.startswith("...") for arg in current_lambda.arg_names)
            arg_names = [arg.lstrip("...") for arg in current_lambda.arg_names.copy()]

            # more arguments than parameters
            if len(current_args) > len(arg_names) and not catch_rest:
                # apply all parameters and evaluate the body
                filled_env = new_env.copy()
                filled_env.update(zip(arg_names, current_args[: len(arg_names)]))
                result = self._eval(
                    current_lambda.body, is_tail=True, state=state.edit(env=filled_env)
                )

                # if result is callable, call it with remaining args
                if isinstance(result, (Lambda, BuiltinFunc)) or hasattr(
                    result, "__call__"
                ):
                    remaining_args = current_args[len(arg_names) :]
                    if isinstance(result, Lambda):
                        # tail-call to a lambda: continue loop with new function and args
                        current_lambda = result
                        current_args = remaining_args
                        current_env = state.env
                        continue
                    else:
                        return result(*remaining_args)  # type: ignore
                else:
                    self.exception(
                        nTypeError,
                        f"Cannot apply {len(current_args) - len(arg_names)} more arguments to non-callable result",
                        pos=call_pos if call_pos else current_lambda.pos,
                        state=state,
                    )

            # handle partial application
            elif len(current_args) < len(arg_names):
                return self._partial_lambda(
                    current_lambda,
                    args=current_args,
                    state=state.edit(env=new_env),
                )

            # exact match: apply all arguments
            else:
                if catch_rest:
                    new_env.update(
                        zip(arg_names[:-1], current_args[: len(arg_names[:-1])])
                    )
                    new_env[arg_names[-1]] = List(current_args[len(arg_names[:-1]) :])
                else:
                    new_env.update(zip(arg_names, current_args))

                result = self._eval(
                    current_lambda.body, is_tail=True, state=state.edit(env=new_env)
                )

                if isinstance(result, Bounce):
                    if isinstance(result.func, Lambda):
                        current_lambda = result.func
                        current_args = result.args
                        current_env = result.env
                        continue
                return result

    def _number(self, this: Number, state: State = State()):
        return mpmath.mpf(this.value)

    def _string(self, this: String, state: State = State()):
        return this.value

    def _constant(self, this: Constant, state: State = State()):
        return self._eval(this.value, state=state)

    def _bool(self, this: Bool, state: State = State()):
        return this.value

    def _printoutput(self, this: PrintOutput, state: State = State()):
        if this.printed:
            return this.expr
        else:
            self.put(self.get_repr(this.expr, state=state) + this.end)
            return PrintOutput(
                self._eval(this.expr, state=state),  # type: ignore
                end=this.end,
                printed=True,
            )

    def _eval(
        self, node: Expr | BuiltinFunc, is_tail: bool = False, state: State = State()
    ):
        if (
            hasattr(node, "pos")
            and hasattr(node.pos, "index")  # type: ignore
            and node.pos.index is not None  # type: ignore
        ):
            state = state.edit(index=node.pos.index)  # type: ignore
        if isinstance(node, Lambda):
            # Don't re-evaluate lambdas that already have a curry environment
            if hasattr(node, "curry") and node.curry:
                curry = node.curry.copy() | state.env
            else:
                curry = state.env.copy()

            lambda_copy = Lambda(
                arg_names=node.arg_names,
                body=node.body,
                curry=curry,
                tree=node.tree,
                pos=dataclasses.replace(
                    node.pos,
                    module=state.module
                    if self.modules[state.module].depth
                    >= self.modules.get(
                        node.pos.module,  # type: ignore
                        self.modules[state.module],
                    ).depth
                    else node.pos.module,
                ),
            )
            return lambda_copy
        elif isinstance(node, (float, int, mpmath.mpf)):
            return mpmath.mpf(node)
        elif (
            isinstance(node, str)
            or type(node).__name__
            == "constant"  # for some reason,  mpmath.ctx_mp_python.constant is not available
        ):
            return node
        elif node is None:
            return mpmath.mpf(0)
        try:
            name = type(node).__name__.lower()
            return getattr(self, "_" + name)(
                node,
                **(
                    {"is_tail": is_tail}
                    if name in ("lambda", "conditional", "call")
                    else {}
                ),
                state=state,
            )
        except AttributeError as e:
            raise e

    def get_repr(self, node: Expr, state: State = State()) -> Any:
        if isinstance(node, (Number, mpmath._ctx_mp._mpf)):
            return (
                node.value.removesuffix(".0")
                if isinstance(node, Number)
                else mpmath.nstr(node, self.precision).removesuffix(".0")  # type: ignore
            )
        elif isinstance(node, (bool, Bool)):
            return "true" if node else "false"
        elif isinstance(node, String):
            return node.value
        elif isinstance(node, Lambda):
            return reconstruct(node, precision=self.precision, env={})
        elif isinstance(node, List):
            elements = [
                self._eval(arg, state=state.edit(env=node.curry))  # type: ignore
                for arg in node.elements
            ]
            for i, res in enumerate(elements):
                if isinstance(res, mpmath.mpf):
                    elements[i] = Number(mpmath.nstr(res, self.precision))  # type: ignore
                elif isinstance(res, bool):
                    elements[i] = Bool(res)
                elif isinstance(res, str):
                    elements[i] = String(res)
                elif isinstance(res, (List, Lambda)):
                    elements[i] = self.get_repr(res, state=state)
            return repr(List(elements))  # type:ignore
        elif node is not None:
            return str(node)

    def run(
        self,
        tree: list[Expr],
        path: str | Path | None,
        code: str = "",
        env: dict[str, Expr] = {},
        modules: dict[str, Module] = {},  # for REPL persistence
    ):
        if path and not str(path).endswith("/") and not code:
            try:
                code = open(path, "r", encoding="utf-8").read()
            except FileNotFoundError:
                pass

        path = str(path) if path else "unknown"
        pos = None

        try:
            self.modules = ImportResolver().resolve(tree, path=path, code=code)
            self.module_id = list(self.modules.keys())[-1]
            self._merge_modules(modules)
            self.modules[self.module_id].globals = env

            for module_id, module in self.modules.items():
                self.validate_exports(module)
                module.globals.update(
                    {c.name: c.value for c in module.tree if isinstance(c, Constant)}
                )

            for node in tree:
                pos = node.pos  # type:ignore
                if isinstance(node, Constant):
                    self.modules[self.module_id].globals[node.name] = self._eval(
                        node.value, state=State({}, self.module_id, tree.index(node))
                    )
                elif isinstance(node, Delete):
                    del self.modules[self.module_id].globals[node.name]
                elif isinstance(node, (Import, Export)):
                    pass
                else:
                    o = self._eval(
                        node, state=State(env, self.module_id, tree.index(node))
                    )
                    if o is not None and not isinstance(o, PrintOutput):
                        self.put(
                            self.get_repr(
                                o,  # type:ignore
                                state=State(env, self.module_id, tree.index(node)),
                            )
                            + "\n"
                        )

            if self.output and not self.output[-1].endswith("\n"):
                self.put("\n")

        except SystemExit:
            if self.fatal:
                sys.exit(1)

        except RecursionError:
            self.exception(
                nRecursionError,
                "maximum recursion depth exceeded",
                pos=Pos(pos.start, None) if pos else None,
                line_only=True,
                state=State(module=self.module_id),
            )

        return self.output
