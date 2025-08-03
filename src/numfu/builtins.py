import operator
from dataclasses import dataclass
from typing import Any

import mpmath as mpm

from .ast_types import List
from .typechecks import BuiltinFunc, Validators

Num = mpm.mpf


def overload(name):
    return BuiltinFunc(name)


@dataclass(frozen=True)
class Builtins:
    pi = mpm.pi
    e = mpm.e

    _add = overload("+")
    _sub = overload("-")
    _mul = overload("*")
    _div = overload("/")
    _mod = overload("%")
    _pow = overload("^")
    _and = overload("&&")
    _or = overload("||")
    _not = overload("!")
    _eq = overload("==")
    _ne = overload("!=")
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
    ceil = overload("ceil")
    floor = overload("floor")
    sign = overload("sign")
    abs = overload("abs")


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
    [None, Validators.mul_integer],
    commutative=True,
).error([str, str], "Cannot multiply two strings")
Builtins._div.add([Num, Num], Num, mpm.fdiv)
Builtins._mod.add([Num, Num], Num, mpm.fmod)
Builtins._pow.add([Num, Num], Num, mpm.power)
Builtins._and.add([Any, Any], bool, lambda a, b: bool(a) and bool(b))
Builtins._or.add([Any, Any], bool, lambda a, b: bool(a) or bool(b))
Builtins._not.add([Any], bool, lambda a: not bool(a))
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
Builtins.ceil.add([Num], Num, mpm.ceil)
Builtins.floor.add([Num], Num, mpm.floor)
Builtins.sign.add([Num], Num, mpm.sign)
Builtins.abs.add([Num], Num, mpm.fabs)
