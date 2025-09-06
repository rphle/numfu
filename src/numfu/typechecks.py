"""
Type Checking and Built-in Function Infrastructure
"""

import itertools
import re
from dataclasses import dataclass
from types import UnionType
from typing import Any, Callable, get_args

import mpmath as mpm

from .ast_types import Call, List, Pos
from .classes import Module, State
from .errors import nAssertionError, nIndexError, nRuntimeError, nTypeError

OPERATORS = (
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
)


def check_type(val, typ):
    if typ is Any:
        return True
    if isinstance(typ, tuple):
        return any(check_type(val, t) for t in typ)
    if isinstance(typ, UnionType):
        return any(check_type(val, t) for t in get_args(typ))
    if isinstance(typ, ListOf):
        return isinstance(val, (list, List)) and all(
            check_type(item, typ.element_type) for item in val
        )
    if typ.__name__ == "mpf" and getattr(val, "name", None) in ("e", "pi"):
        return True
    return isinstance(val, typ)


def type_name(t):
    if t is Any:
        return "any"
    match t:
        case tuple():
            return " or ".join(type_name(x) for x in t)
        case UnionType():
            return " or ".join(type_name(x) for x in get_args(t))
        case list() | "list" | List():
            return "List"
        case mpm._ctx_mp._mpf():
            return "Number"
        case str():
            return "String"
        case bool():
            return "Boolean"

    names = {"str": "String", "mpf": "Number", "list": "List", "bool": "Boolean"}
    return names.get(getattr(t, "__name__", str(t)), getattr(t, "__name__", str(t)))


@dataclass
class HelpMsg:
    invalid_arg: str = ""
    arg_num: str = ""


class ListOf:
    """
    Generic type for homogeneous lists: List<Number>, List<String>, etc.
    """

    def __init__(self, element_type):
        self.element_type = element_type

    def __repr__(self):
        return f"List<{type_name(self.element_type)}>"


class InfiniteOf:
    """
    Type for functions accepting unlimited arguments of one type.
    """

    def __init__(self, element_type):
        self.element_type = element_type


@dataclass
class Validators:
    @staticmethod
    def mul_integer(x):
        """Can't multiply by non-integer"""
        try:
            return isinstance(x, mpm.mpf) and x == int(x)
        except Exception:
            return False

    @staticmethod
    def is_iterable(x):
        """Type '{typename}' is not iterable"""
        return hasattr(x, "__iter__")

    @staticmethod
    def is_number(x):
        """Can't convert to number with base 10: '{arg}'"""
        if isinstance(x, (bool, mpm._ctx_mp._mpf)):
            return True

        return bool(
            re.match(
                r"(-|\+)*((0|[1-9][\d_]*)(\.[\d_]+)?|\.[\d_]+)([eE][+-]?[\d_]+)?", x
            )
        )

    @staticmethod
    def list_index(x):
        """List index must be an integer"""
        try:
            return isinstance(x, mpm.mpf) and x == int(x)
        except Exception:
            return False

    @staticmethod
    def string_index(x):
        """String index must be an integer"""
        try:
            return isinstance(x, mpm.mpf) and x == int(x)
        except Exception:
            return False

    @staticmethod
    def is_integer(x):
        """Argument {i} must be an integer"""
        try:
            return isinstance(x, mpm.mpf) and x == int(x)
        except Exception:
            return False


class BuiltinFunc:
    """
    Represents a built-in function with multiple type overloads.

    Built-in functions can accept different combinations of argument types
    and return appropriate results. Handles type checking,
    validation, and dispatch to the correct implementation.

    Args:
        name: Function name as it appears in NumFu
        eval_lists: Whether to evaluate list elements before processing
        help: Additional help messages for error reporting
    """

    def __init__(
        self,
        name,
        eval_lists: bool = False,
        help: HelpMsg = HelpMsg(),
        partial: bool = False,
    ):
        self.name = name
        self.eval_lists = eval_lists
        self.help = help
        self.partial = partial
        self.is_operator = self.name in OPERATORS
        self._overloads = []
        self._errors = []

    def add(
        self,
        arg_types,
        return_type,
        func,
        validators: list[Callable[[Any], bool] | None] = [],
        transformer: Callable[[Any], Any] | None = None,
        commutative=False,
        help: HelpMsg = HelpMsg(),
    ):
        """
        Register a type overload for a built-in function.

        Args:
            arg_types: List of expected argument types
            return_type: Expected return type
            func: Function to call
            validators: Optional validation functions for arguments
            transformer: Optional argument transformation function
            commutative: Whether to generate permutations for commutative operations
            help: Specific help for this overload
        """

        if validators and len(arg_types) != len(validators):
            raise ValueError("Number of argument types must match number of validators")
        if any(isinstance(a, InfiniteOf) for a in arg_types):
            if sum(isinstance(a, InfiniteOf) for a in arg_types) > 1:
                raise ValueError("Cannot have more than one InfiniteOf type")
            if not isinstance(arg_types[-1], InfiniteOf):
                raise ValueError("InfiniteOf type must be last")
        if commutative:
            for perm in itertools.permutations(range(len(arg_types))):
                self._overloads.append(
                    (
                        [arg_types[i] for i in perm],
                        return_type,
                        (lambda f, p: lambda *a: f(*[a[i] for i in p]))(
                            func, perm
                        ),  # also permute the arguments
                        help,
                        [validators[i] for i in perm] if validators else [],
                        transformer,
                    )
                )
        else:
            self._overloads.append(
                (arg_types, return_type, func, help, validators, transformer)
            )
        return self

    def error(self, arg_types, error: str):
        self._errors.append((arg_types, error))
        return self

    def exception(
        self,
        message: str,
        module: Module,
        args_pos: Pos = Pos(),
        func_pos: Pos = Pos(),
    ):
        nTypeError(
            message,
            func_pos if self.is_operator else args_pos,
            module=module,
        )

    def __call__(
        self,
        *args,
        module: Module = Module(),
        args_pos: Pos = Pos(),
        func_pos: Pos = Pos(),
        precision: int = 15,
        interpreter=None,
        state: State = State(),
    ):
        errors = []
        for arg_types, _, func, help, validators, transformer in self._overloads:
            if arg_types and isinstance(arg_types[-1], InfiniteOf):
                arg_types = arg_types[:-1] + (
                    [arg_types[-1].element_type] * (len(args) - len(arg_types) + 1)
                )

            if len(args) != len(arg_types):
                continue

            if transformer:
                args = transformer(*args)

            for i, (arg, typ) in reversed(list(enumerate(zip(args, arg_types)))):
                if not check_type(arg, typ):
                    errors.append(
                        f"Invalid argument type for {'operator ' if self.is_operator else ''}'{self.name}': "
                        f"argument {i+1} must be {type_name(typ)}, got {type_name(arg)}"
                        + (f"\nhelp: {help.invalid_arg}" if help.invalid_arg else "")
                    )
                    break

                if validators and validators[i] and not validators[i](arg):
                    v = validators[i]
                    doc = (getattr(v, "__doc__", "") or "").strip()
                    self.exception(
                        doc.format(i=i + 1, typename=type_name(arg), arg=arg),
                        module=module,
                        func_pos=func_pos,
                        args_pos=args_pos,
                    )
                    break

            else:
                if not self.partial:
                    if self.name in ("String", "format"):
                        try:
                            return func(*args, precision=precision)
                        except IndexError as e:
                            if self.name == "format":
                                nIndexError(
                                    "Incorrect number of placeholders",
                                    args_pos,
                                    module=module,
                                )
                            else:
                                raise e
                    elif self.name == "error":
                        nRuntimeError(
                            args[0],
                            Pos(func_pos.start, args_pos.end),
                            module=module,
                            name=args[1] if len(args) == 2 else None,
                        )
                    elif self.name == "assert":
                        if not args[0]:
                            nAssertionError(
                                "",
                                args_pos,
                                module=module,
                            )
                        else:
                            return True if len(args) == 1 else args[1]
                    elif self.name == "filter":
                        if not interpreter:
                            raise ValueError(
                                "Missing interpreter reference for filter builtin function"
                            )
                        return List(
                            [
                                e
                                for e in args[0].elements
                                if interpreter._eval(
                                    Call(func=args[1], args=[e], pos=func_pos),
                                    state=state.edit(env=state.env | args[0].curry),
                                )
                            ],
                            pos=args[0].pos,
                            curry=args[0].curry,
                        )
                    elif self.name == "range":
                        return List(
                            [mpm.mpf(i) for i in range(int(args[0]), int(args[1]))],
                            pos=func_pos,
                        )
                    elif self.name == "set" and isinstance(args[0], List):
                        lst, i, value = args
                        try:
                            lst.elements[int(i)] = value
                        except IndexError:
                            nIndexError("Index out of range", args_pos, module)
                        return lst

                return func(*args)

        for arg_types, message in self._errors:
            if all(check_type(arg, typ) for arg, typ in zip(args, arg_types)):
                self.exception(
                    message,
                    module=module,
                    func_pos=func_pos,
                    args_pos=args_pos,
                )

        if errors:
            self.exception(
                errors[0], module=module, func_pos=func_pos, args_pos=args_pos
            )

        expected_count = len(self._overloads[0][0]) if self._overloads else 0
        self.exception(
            f"'{self.name}' expected {expected_count} argument{'s' if expected_count != 1 else ''}, got {len(args)}"
            + (f"\nhelp: {self.help.arg_num}" if self.help.arg_num else ""),
            module=module,
            func_pos=func_pos,
            args_pos=args_pos,
        )

    def __repr__(self) -> str:
        return f"{'Partial' if self.partial else ''}BuiltinFunction"
