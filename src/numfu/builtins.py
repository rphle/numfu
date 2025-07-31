import operator
from dataclasses import dataclass
from types import UnionType
from typing import Callable

import mpmath as mpm

Operators = {
    "_add": "+",
    "_sub": "-",
    "_mul": "*",
    "_div": "/",
    "_mod": "%",
    "_pow": "^",
    "_and": "&&",
    "_or": "||",
    "_not": "!",
    "_gt": ">",
    "_lt": "<",
    "_ge": ">=",
    "_le": "<=",
    "_eq": "==",
    "_ne": "!=",
}


class BuiltinFunc:
    def __init__(
        self,
        func: Callable,
        args: type | UnionType,
        returns: type,
        name: str | None = None,
    ):
        self.func = func
        self.args = args
        self.returns = returns
        self.name = name if name is not None else func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


def _mpf2mpf(x, n: str | None = None):
    return BuiltinFunc(x, mpm.mpf, mpm.mpf, name=n)


def _mpf2bool(x, n: str | None = None):
    return BuiltinFunc(x, mpm.mpf, bool, name=n)


def _any2bool(x, n: str | None = None):
    return BuiltinFunc(x, mpm.mpf | bool, bool, name=n)


@dataclass
class Builtins:
    # Constants
    pi = mpm.pi
    e = mpm.e

    # Arithmetic
    _add = _mpf2mpf(mpm.fadd, n="+")
    _sub = _mpf2mpf(
        lambda a, b=None: mpm.fsub(0, a) if b is None else mpm.fsub(a, b), n="-"
    )
    _mul = _mpf2mpf(mpm.fmul, n="*")
    _div = _mpf2mpf(mpm.fdiv, n="/")
    _mod = _mpf2mpf(mpm.fmod, n="%")
    _pow = _mpf2mpf(mpm.power, n="^")

    # Logic
    _and = _any2bool(lambda a, b: bool(a) and bool(b), n="&&")
    _or = _any2bool(lambda a, b: bool(a) or bool(b), n="||")
    _not = _any2bool(lambda a: not bool(a), n="!")

    # Comparison
    _gt, _lt, _ge, _le, _eq, _ne = map(
        lambda x: _mpf2bool(
            x,
            n={"gt": ">", "lt": "<", "ge": ">=", "le": "<=", "eq": "==", "ne": "!="}[
                x.__name__
            ],
        ),
        [operator.gt, operator.lt, operator.ge, operator.le, operator.eq, operator.ne],
    )

    # Trigonometry
    sin, cos, tan = map(_mpf2mpf, (mpm.sin, mpm.cos, mpm.tan))
    asin, acos, atan, atan2 = map(_mpf2mpf, (mpm.asin, mpm.acos, mpm.atan, mpm.atan2))

    # Hyperbolic
    sinh, cosh, tanh = map(_mpf2mpf, (mpm.sinh, mpm.cosh, mpm.tanh))
    asinh, acosh, atanh = map(_mpf2mpf, (mpm.asinh, mpm.acosh, mpm.atanh))

    # Exponential & Log
    exp, log, log10, sqrt = map(_mpf2mpf, (mpm.exp, mpm.log, mpm.log10, mpm.sqrt))

    # Rounding / Sign
    ceil, floor, sign = map(_mpf2mpf, (mpm.ceil, mpm.floor, mpm.sign))
    abs = _mpf2mpf(mpm.fabs, n="abs")
