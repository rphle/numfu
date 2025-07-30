import operator
from dataclasses import dataclass

import mpmath

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


@dataclass
class Builtins:
    # Constants
    pi = mpmath.pi
    e = mpmath.e

    # Arithmetic
    _add = staticmethod(mpmath.fadd)
    _sub = staticmethod(
        lambda a, b=None: mpmath.fsub(0, a) if b is None else mpmath.fsub(a, b)
    )
    _mul = staticmethod(mpmath.fmul)
    _div = staticmethod(mpmath.fdiv)
    _mod = staticmethod(mpmath.fmod)
    _pow = staticmethod(mpmath.power)

    # Logic
    _and = staticmethod(lambda a, b: bool(a) and bool(b))
    _or = staticmethod(lambda a, b: bool(a) or bool(b))
    _not = staticmethod(lambda a: not bool(a))

    # Comparison
    _gt, _lt, _ge, _le, _eq, _ne = map(
        staticmethod,
        [operator.gt, operator.lt, operator.ge, operator.le, operator.eq, operator.ne],
    )

    # Trigonometry
    sin, cos, tan = map(staticmethod, (mpmath.sin, mpmath.cos, mpmath.tan))
    asin, acos, atan, atan2 = map(
        staticmethod, (mpmath.asin, mpmath.acos, mpmath.atan, mpmath.atan2)
    )

    # Hyperbolic
    sinh, cosh, tanh = map(staticmethod, (mpmath.sinh, mpmath.cosh, mpmath.tanh))
    asinh, acosh, atanh = map(staticmethod, (mpmath.asinh, mpmath.acosh, mpmath.atanh))

    # Exponential & Log
    exp, log, log10 = map(staticmethod, (mpmath.exp, mpmath.log, mpmath.log10))
    sqrt = staticmethod(mpmath.sqrt)

    # Rounding / Sign
    ceil, floor, fabs, sign = map(
        staticmethod, (mpmath.ceil, mpmath.floor, mpmath.fabs, mpmath.sign)
    )
