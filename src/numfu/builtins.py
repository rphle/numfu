"""
Built-in Functions and Operations

Implements all built-in functions, operators, and constants
available in NumFu programs. Functions are implemented as type-safe overloaded
operations that can handle multiple argument types.
"""

import operator
import random
import re
import sys
import time
from dataclasses import dataclass
from typing import Any

import mpmath as mpm

from .ast_types import Call, Lambda, List, PrintOutput, Variable
from .reconstruct import reconstruct
from .typechecks import BuiltinFunc, HelpMsg, InfiniteOf, ListOf, Validators

Num = mpm.mpf
mpm.e.name = "e"


def overload(name, eval_lists: bool = False, help: HelpMsg = HelpMsg()):
    """
    Create a built-in function that can handle multiple argument types.

    Args:
        name: Function name as it appears in NumFu
        eval_lists: Whether to evaluate list elements before calling
        help: Help messages for error reporting

    Returns:
        BuiltinFunc instance that can be registered with type overloads
    """
    return BuiltinFunc(name, eval_lists, help)


def to_string(x, precision):
    if isinstance(x, mpm._ctx_mp._mpf):
        return str(mpm.nstr(x, n=precision)).removesuffix(".0")  # type: ignore
    elif isinstance(x, bool):
        return "true" if x else "false"
    elif isinstance(x, Lambda):
        return reconstruct(x, precision=precision, env=x.curry)
    else:
        return str(x)


def division(a, b):
    """
    Safe division that handles division by zero according to IEEE 754.
    """
    try:
        return mpm.fdiv(a, b)
    except ZeroDivisionError:
        if a == 0:
            return mpm.mpf("nan")
        elif a > 0:
            return mpm.mpf("inf")
        else:
            return mpm.mpf("-inf")


@dataclass(frozen=True)
class Builtins:
    nan = mpm.nan
    inf = mpm.inf

    _add = overload("+")
    _sub = overload("-")
    _mul = overload("*")
    _div = overload("/")
    _mod = overload("%")
    _pow = overload("^")

    _and = overload("&&")
    _or = overload("||")
    _not = overload("!")
    _xor = overload("xor")

    _eq = overload("==", eval_lists=True)
    _ne = overload("!=", eval_lists=True)
    _gt = overload(">")
    _lt = overload("<")
    _ge = overload(">=")
    _le = overload("<=")

    _map = overload("map")
    _filter = overload("filter")

    _error = overload("error")
    _assert = overload("assert", eval_lists=True)
    _exit = overload("exit")


@dataclass(frozen=True)
class Math:
    pi = mpm.pi
    e = mpm.e

    sin = overload("sin")
    cos = overload("cos")
    tan = overload("tan")
    asin = overload("asin")
    acos = overload("acos")
    atan = overload("atan")
    atan2 = overload("atan2")

    sinh = overload("sinh")
    cosh = overload("cosh")
    tanh = overload("tanh")
    asinh = overload("asinh")
    acosh = overload("acosh")
    atanh = overload("atanh")

    exp = overload("exp")
    log = overload("log")
    log10 = overload("log10")
    sqrt = overload("sqrt")

    _ceil = overload("ceil")
    _floor = overload("floor")
    _round = overload("round")
    _sign = overload("sign")
    _abs = overload("abs")
    _max = overload("max", eval_lists=True)
    _min = overload("min", eval_lists=True)

    _sum = overload("sum", eval_lists=True)

    _radians = overload("radians")
    _degrees = overload("degrees")


@dataclass(frozen=True)
class Types:
    _isnan = overload("isnan")
    _isinf = overload("isinf")

    _bool = overload("Bool")
    _number = overload("Number")
    _list = overload("List")
    _string = overload("String")


@dataclass(frozen=True)
class Std:
    _append = overload("append")
    _length = overload("length")
    _contains = overload("contains", eval_lists=True)
    _set = overload("set")
    _reverse = overload("reverse")
    _sort = overload("sort", eval_lists=True)
    _slice = overload("slice")
    _join = overload("join", eval_lists=True)
    _split = overload("split")

    _format = overload("format")
    _trim = overload("trim")
    _toLowerCase = overload("toLowerCase")
    _toUpperCase = overload("toUpperCase")
    _replace = overload("replace")
    _count = overload("count")

    _range = overload("range")


@dataclass(frozen=True)
class Io:
    _print = overload("print")
    _println = overload("println")
    _input = overload("input")


@dataclass(frozen=True)
class Random:
    _random = overload("random")
    _seed = overload("seed")


@dataclass(frozen=True)
class System:
    _time = overload("time")


# Register overloads
Builtins._add.add([Num, Num], Num, mpm.fadd).add([str, str], str, operator.add).add(
    [List, List],
    List,
    lambda a, b: List(a.elements + b.elements, pos=a.pos, curry=a.curry | b.curry),
)
Builtins._sub.add([Num], Num, lambda a: mpm.fsub(0, a)).add([Num, Num], Num, mpm.fsub)
Builtins._mul.add([Num, Num], Num, mpm.fmul).add(
    [str, Num],
    str,
    lambda a, b: a * int(b),
    validators=[None, Validators.mul_integer],
    commutative=True,
).add(
    [List, Num],
    List,
    lambda a, b: List(a.elements * int(b), pos=a.pos, curry=a.curry),
    validators=[None, Validators.mul_integer],
    commutative=True,
).error([str, str], "Cannot multiply two strings").error(
    [List, List], "Cannot multiply two lists"
)
Builtins._div.add([Num, Num], Num, division)
Builtins._mod.add([Num, Num], Num, mpm.fmod)
Builtins._pow.add([Num, Num], Num, mpm.power)

Builtins._and.add([Any, Any], bool, lambda a, b: bool(a) and bool(b))
Builtins._or.add([Any, Any], bool, lambda a, b: bool(a) or bool(b))
Builtins._not.add([Any], bool, lambda a: not bool(a))
Builtins._xor.add([Any, Any], bool, lambda a, b: bool(a) ^ bool(b))

Builtins._eq.add(
    [Any, Any],
    bool,
    lambda a, b: mpm.almosteq(a, b)
    if isinstance(a, Num) and isinstance(b, Num)
    else a == b,
)
Builtins._ne.add([Any, Any], bool, operator.ne)
Builtins._gt.add([Num, Num], bool, operator.gt)
Builtins._lt.add([Num, Num], bool, operator.lt)
Builtins._ge.add([Num, Num], bool, operator.ge)
Builtins._le.add([Num, Num], bool, operator.le)

Math.sin.add([Num], Num, mpm.sin)
Math.cos.add([Num], Num, mpm.cos)
Math.tan.add([Num], Num, mpm.tan)
Math.asin.add([Num], Num, mpm.asin)
Math.acos.add([Num], Num, mpm.acos)
Math.atan.add([Num], Num, mpm.atan)
Math.atan2.add([Num, Num], Num, mpm.atan2)

Math.sinh.add([Num], Num, mpm.sinh)
Math.cosh.add([Num], Num, mpm.cosh)
Math.tanh.add([Num], Num, mpm.tanh)
Math.asinh.add([Num], Num, mpm.asinh)
Math.acosh.add([Num], Num, mpm.acosh)
Math.atanh.add([Num], Num, mpm.atanh)

Math.exp.add([Num], Num, mpm.exp)
Math.log.add([Num, Num], Num, mpm.log)
Math.log10.add([Num], Num, mpm.log10)
Math.sqrt.add([Num], Num, mpm.sqrt)
Math._max.add([InfiniteOf(Num)], Num, max).add(
    [ListOf(Num)],
    Num,
    max,
    transformer=lambda x: [x.elements],
    help=HelpMsg(invalid_arg="Only numbers are supported"),
)
Math._min.add([InfiniteOf(Num)], Num, min).add(
    [ListOf(Num)],
    Num,
    min,
    transformer=lambda x: [x.elements],
    help=HelpMsg(invalid_arg="Only numbers are supported"),
)
Math._sum.add([ListOf(Num)], Num, sum)

Math._radians.add([Num], Num, mpm.radians)
Math._degrees.add([Num], Num, mpm.degrees)

Types._isnan.add([Num], Num, mpm.isnan)
Types._isinf.add([Num], bool, mpm.isinf)

Math._ceil.add([Num], Num, mpm.ceil)
Math._floor.add([Num], Num, mpm.floor)
Math._round.add([Num], Num, lambda x: Num(round(x))).add(
    [Num, Num],
    Num,
    lambda x, p: Num(round(x, int(p)), validators=[None, Validators.is_integer]),
)
Math._sign.add([Num], Num, mpm.sign)
Math._abs.add([Num], Num, mpm.fabs)

Types._bool.add([Any], bool, lambda a: bool(a))
Types._number.add(
    [bool | Num | str],
    Num,
    lambda x: Num(
        re.sub(
            r"^(\+|-)*",
            "" if x.split("e")[0].split("E")[0].count("-") % 2 == 0 else "-",
            x,
        )  # resolve sign chains
        if isinstance(x, str)
        else x
    ),
    validators=[Validators.is_number],
)
Types._list.add([Any], List, lambda a: List(a), validators=[Validators.is_iterable])
Types._string.add([Any], str, to_string)

# Lists & Strings
Std._append.add(
    [List, Any], List, lambda a, b: List(a.elements + [b], pos=a.pos, curry=a.curry)
)
Std._length.add([List | str], Num, lambda a: Num(len(a)))
Std._contains.add([List, Any], bool, lambda a, b: b in a).add(
    [str, str], bool, lambda a, b: b in a
)
Std._set.add(
    [List, Num, Any],
    List,
    lambda: None,
    validators=[None, Validators.list_index, None],
).add(
    [str, Num, str],
    str,
    lambda s, i, v: s[: int(i)] + v + s[int(i) + 1 :],
    validators=[None, Validators.string_index, None],
)
Std._reverse.add(
    [List | str],
    List | str,
    lambda a: a[::-1]
    if isinstance(a, str)
    else List(a.elements[::-1], pos=a.pos, curry=a.curry),
)
Std._sort.add(
    [List],
    List,
    lambda a: List(sorted(a.elements), pos=a.pos, curry=a.curry),
).add(
    [str],
    str,
    lambda a: "".join(sorted(a)),
)
Std._slice.add(
    [List | str, Num, Num],
    List | str,
    lambda a, b, c: a[int(b) : int(c) + 1 if c != -1 else None]
    if isinstance(a, str)
    else List(
        a.elements[int(b) : int(c) + 1 if c != -1 else None], pos=a.pos, curry=a.curry
    ),
    validators=[None, Validators.string_index, Validators.string_index],
)
Std._join.add([ListOf(str), str], str, lambda a, b: b.join(a.elements))
Std._split.add(
    [str, str], List, lambda a, b: List(a.split(b) if b != "" else a.split())
)

Std._format.add(
    [str, InfiniteOf(Any)],
    str,
    lambda a, *args, precision=15: a.format(
        *[to_string(a, precision=precision) for a in args]
    ),
)
Std._trim.add([str], str, lambda s: s.strip())
Std._toLowerCase.add([str], str, lambda s: s.lower())
Std._toUpperCase.add([str], str, lambda s: s.upper())
Std._replace.add([str, str, str], str, lambda a, b, c: a.replace(b, c))
Std._count.add([str, str], Num, lambda a, b: Num(a.count(b)))

Builtins._map.add(
    [List, Lambda | BuiltinFunc],
    List,
    lambda lst, f: List(
        [
            Call(f, [element], pos=f.pos)
            if isinstance(f, Lambda)
            else Call(
                Variable(f.name) if not f.partial else f,
                [element],
                pos=getattr(element, "pos", None),  # type: ignore
            )
            for element in lst.elements
        ],
        pos=lst.pos,
        curry=lst.curry,
    ),
)
Builtins._filter.add(
    [List, Lambda | BuiltinFunc],
    List,
    lambda: None,
)
Std._range.add(
    [Num, Num],
    List,
    lambda: None,
    validators=[Validators.is_integer, Validators.is_integer],
)

Io._println.add(
    [Any],
    Any,
    lambda expr: PrintOutput(expr, end="\n"),
)
Io._print.add(
    [Any],
    Any,
    lambda expr: PrintOutput(expr),
)
Io._input.add(
    [],
    str,
    input,
).add(
    [str],
    str,
    input,
)

Random._random.add([], Num, lambda: Num(random.random()))
Random._seed.add([Num | str], None, random.seed)

Builtins._error.add([str], None, lambda x: None).add([str, str], None, lambda x: None)
Builtins._assert.add([bool], Any, lambda x: None).add([bool, Any], Any, lambda x: None)
Builtins._exit.add([], None, sys.exit)
System._time.add([], Num, lambda: Num(time.time()))
