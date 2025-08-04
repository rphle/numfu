import operator
import random
import re
import sys
import time
from dataclasses import dataclass
from typing import Any

import mpmath as mpm

from .ast_types import Call, Lambda, List, PrintOutput
from .typechecks import BuiltinFunc, HelpMsg, InfiniteOf, ListOf, Validators

Num = mpm.mpf


def overload(name, eval_lists: bool = False, help: HelpMsg = HelpMsg()):
    return BuiltinFunc(name, eval_lists, help)


def to_string(x, precision):
    if isinstance(x, mpm._ctx_mp._mpf):
        return mpm.nstr(x, precision=precision).removesuffix(".0")
    elif isinstance(x, bool):
        return "true" if x else "false"
    else:
        return str(x)


def division(a, b):
    try:
        return mpm.fdiv(a, b)
    except ZeroDivisionError:
        if a == 0:
            return mpm.mpf("nan")
        elif a > 0:
            return mpm.mpf("inf")
        else:
            return mpm.mpf("-inf")


def set_list(i: int, value, lst: List):
    lst.elements[int(i)] = value
    return lst


@dataclass(frozen=True)
class Builtins:
    pi = mpm.pi
    e = mpm.e

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

    _bool = overload("Bool")
    _number = overload("Number")
    _list = overload("List")
    _string = overload("String")

    # Lists & Strings
    _append = overload("append")
    _length = overload("length")
    _member = overload("member")
    _set = overload("set")
    _reverse = overload("reverse")
    _sort = overload("sort", eval_lists=True)
    _slice = overload("slice")
    _join = overload("join", eval_lists=True)
    _split = overload("split")

    _format = overload("format")

    # Functions
    _map = overload("map")
    _filter = overload("filter")

    # Output
    _print = overload("print")
    _println = overload("println")

    # Random
    _random = overload("random")
    _seed = overload("seed")

    # System
    _error = overload("error")
    _assert = overload("assert", eval_lists=True)
    _exit = overload("exit")
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

Builtins._eq.add([Any, Any], bool, operator.eq)
Builtins._ne.add([Any, Any], bool, operator.ne)
Builtins._gt.add([Num, Num], bool, operator.gt)
Builtins._lt.add([Num, Num], bool, operator.lt)
Builtins._ge.add([Num, Num], bool, operator.ge)
Builtins._le.add([Num, Num], bool, operator.le)

Builtins.sin.add([Num], Num, mpm.sin)
Builtins.cos.add([Num], Num, mpm.cos)
Builtins.tan.add([Num], Num, mpm.tan)
Builtins.asin.add([Num], Num, mpm.asin)
Builtins.acos.add([Num], Num, mpm.acos)
Builtins.atan.add([Num], Num, mpm.atan)
Builtins.atan2.add([Num, Num], Num, mpm.atan2)

Builtins.sinh.add([Num], Num, mpm.sinh)
Builtins.cosh.add([Num], Num, mpm.cosh)
Builtins.tanh.add([Num], Num, mpm.tanh)
Builtins.asinh.add([Num], Num, mpm.asinh)
Builtins.acosh.add([Num], Num, mpm.acosh)
Builtins.atanh.add([Num], Num, mpm.atanh)

Builtins.exp.add([Num], Num, mpm.exp)
Builtins.log.add([Num, Num], Num, mpm.log)
Builtins.log10.add([Num], Num, mpm.log10)
Builtins.sqrt.add([Num], Num, mpm.sqrt)
Builtins._max.add([InfiniteOf(Num)], Num, max).add(
    [ListOf(Num)],
    Num,
    max,
    transformer=lambda x: [x.elements],
    help=HelpMsg(invalid_arg="Only numbers are supported"),
)
Builtins._min.add([InfiniteOf(Num)], Num, min).add(
    [ListOf(Num)],
    Num,
    min,
    transformer=lambda x: [x.elements],
    help=HelpMsg(invalid_arg="Only numbers are supported"),
)

Builtins._ceil.add([Num], Num, mpm.ceil)
Builtins._floor.add([Num], Num, mpm.floor)
Builtins._round.add([Num], Num, lambda x: Num(round(x))).add(
    [Num, Num],
    Num,
    lambda x, p: Num(round(x, int(p)), validators=[None, Validators.is_integer]),
)
Builtins._sign.add([Num], Num, mpm.sign)
Builtins._abs.add([Num], Num, mpm.fabs)

Builtins._bool.add([Any], bool, lambda a: bool(a))
Builtins._number.add(
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
Builtins._list.add([Any], List, lambda a: List(a), validators=[Validators.is_iterable])
Builtins._string.add([Any], str, to_string)

# Lists & Strings
Builtins._append.add(
    [List, Any], List, lambda a, b: List(a.elements + [b], pos=a.pos, curry=a.curry)
)
Builtins._length.add([List | str], Num, lambda a: len(a))
Builtins._member.add([Any, List], bool, lambda a, b: a in b).add(
    [str, str], bool, lambda a, b: a in b
)
Builtins._set.add(
    [List, Num, Any],
    List,
    set_list,
    validators=[None, Validators.list_index, None],
).add(
    [str, Num, str],
    str,
    lambda s, i, v: s[: int(i)] + v + s[int(i) + 1 :],
    validators=[None, Validators.string_index, None],
)
Builtins._reverse.add(
    [List | str],
    List | str,
    lambda a: a[::-1]
    if isinstance(a, str)
    else List(a.elements[::-1], pos=a.pos, curry=a.curry),
)
Builtins._sort.add(
    [List],
    List,
    lambda a: List(sorted(a.elements), pos=a.pos, curry=a.curry),
).add(
    [str],
    str,
    lambda a: "".join(sorted(a)),
)
Builtins._slice.add(
    [List | str, Num, Num],
    List | str,
    lambda a, b, c: a[int(b) : int(c) + 1 if c != -1 else None]
    if isinstance(a, str)
    else List(
        a.elements[int(b) : int(c) + 1 if c != -1 else None], pos=a.pos, curry=a.curry
    ),
    validators=[None, Validators.string_index, Validators.string_index],
)
Builtins._join.add([List, str], str, lambda a, b: b.join(a.elements))
Builtins._split.add([str, str], List, lambda a, b: List(a.split(b)))
Builtins._format.add(
    [str, InfiniteOf(str)],
    str,
    lambda a, *args: a.format(*args),
)

Builtins._map.add(
    [List, Lambda],
    List,
    lambda lst, f: List(
        [Call(f, [element], pos=f.pos) for element in lst.elements],
        pos=lst.pos,
        curry=lst.curry,
    ),
)
Builtins._filter.add(
    [List, Lambda],
    List,
    lambda: None,
)

Builtins._println.add(
    [Any],
    Any,
    lambda expr: PrintOutput(expr, end="\n"),
)
Builtins._print.add(
    [Any],
    Any,
    lambda expr: PrintOutput(expr),
)

Builtins._random.add([], Num, lambda: Num(random.random()))
Builtins._seed.add([Num | str], None, random.seed)

Builtins._error.add([str], None, lambda x: None).add([str, str], None, lambda x: None)
Builtins._assert.add([bool], Any, lambda x: None).add([bool, Any], Any, lambda x: None)
Builtins._exit.add([], None, sys.exit)
Builtins._time.add([], Num, lambda: Num(time.time()))
