from dataclasses import dataclass
from types import UnionType
from typing import Any, get_args

import mpmath as mpm

from .errors import ErrorMeta, Pos, nTypeError


def type_matches(val, typ):
    if typ is Any:
        return True
    if isinstance(typ, tuple):
        return any(type_matches(val, t) for t in typ)
    if isinstance(typ, UnionType):
        return any(type_matches(val, t) for t in get_args(typ))
    return isinstance(val, typ)


def type_name(t):
    if t is Any:
        return "any"
    match t:
        case tuple():
            return " or ".join(type_name(x) for x in t)
        case UnionType():
            return " or ".join(type_name(x) for x in get_args(t))
        case list() | "list":
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
class Validators:
    @staticmethod
    def mul_integer(x):
        """Can't multiply by non-integer"""
        try:
            return isinstance(x, mpm.mpf) and x == int(x)
        except Exception:
            return False


class BuiltinFunc:
    def __init__(self, name):
        self.name = name
        self.is_operator = len(self.name) == 1
        self._overloads = []
        self._errors = []

    def add(self, arg_types, return_type, func, validators=None):
        self._overloads.append((arg_types, return_type, func, validators))
        return self

    def error(self, arg_types, error: str):
        self._errors.append((arg_types, error))

    def exception(
        self,
        message: str,
        errormeta: ErrorMeta,
        args_pos: Pos | None = None,
        func_pos: Pos | None = None,
    ):
        nTypeError(
            message,
            func_pos if self.is_operator else args_pos,
            errormeta=errormeta,
        )

    def __call__(
        self,
        *args,
        errormeta: ErrorMeta = ErrorMeta(),
        args_pos: Pos | None = None,
        func_pos: Pos | None = None,
    ):
        errors = []

        for arg_types, _, func, validators in self._overloads:
            if len(args) != len(arg_types):
                continue

            for i, (arg, typ) in reversed(list(enumerate(zip(args, arg_types)))):
                if validators and validators[i] and not validators[i](arg):
                    v = validators[i]
                    doc = (getattr(v, "__doc__", "") or "").strip()
                    self.exception(
                        doc.format(i + 1),
                        errormeta=errormeta,
                        func_pos=func_pos,
                        args_pos=args_pos,
                    )

                if not type_matches(arg, typ):
                    errors.append(
                        f"Invalid argument type for {'operator ' if self.is_operator else ''}'{self.name}': "
                        f"argument {i+1} must be {type_name(typ)}, got {type_name(arg)}"
                    )
                    break

            else:
                return func(*args)

        for arg_types, message in self._errors:
            if all(type_matches(arg, typ) for arg, typ in zip(args, arg_types)):
                self.exception(
                    message, errormeta=errormeta, func_pos=func_pos, args_pos=args_pos
                )

        if errors:
            self.exception(
                errors[-1], errormeta=errormeta, func_pos=func_pos, args_pos=args_pos
            )

        expected_count = len(self._overloads[0][0]) if self._overloads else 0
        self.exception(
            f"'{self.name}' expected {expected_count} argument{'s' if expected_count != 1 else ''}, got {len(args)}",
            errormeta=errormeta,
            func_pos=func_pos,
            args_pos=args_pos,
        )
