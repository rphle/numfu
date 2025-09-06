"""
Code Reconstruction from AST

This module reconstructs NumFu source code from ASTs,
primarily used for displaying partially applied functions and closures
in the REPL. It reverses the parsing process to show readable code.

Lambda AST objects save their Lark parse tree which can be reconstructed
by Lark's reconstructor.
"""

import pickle
import zlib

import lark
import lark.reconstruct
import mpmath

from .ast_types import Lambda, List, Number, String, Variable
from .grammar.grammar import grammar


def tree_repr(node, precision: int = 15, env: dict = {}):
    if isinstance(node, (mpmath.mpf, Number)):
        value = lark.Tree(
            "number",
            [
                lark.Token(
                    "NUMBER",  # type: ignore
                    node.value
                    if isinstance(node, Number)
                    else str(mpmath.nstr(node, precision)).removesuffix(".0"),
                )
            ],  # type: ignore
        )
    elif isinstance(node, Lambda):
        value = pickle.loads(zlib.decompress(node.tree))
    elif isinstance(node, Variable):
        value = env.get(node.name, node)
        value = tree_repr(value, precision=precision, env=env)
    elif isinstance(node, List):
        value = lark.Tree(
            "list_literal",
            [
                lark.Tree(
                    "list_element",
                    [tree_repr(item, precision=precision, env=env | node.curry)],
                )
                for item in node.elements
            ],
        )
    elif isinstance(node, String):
        value = lark.Tree(
            "string",
            [
                lark.Token(
                    "STRING",  # type: ignore
                    node.value,
                )
            ],
        )
    else:
        value = lark.Tree("variable", [node])
    return value


class Resolver(lark.Transformer):
    def __init__(self, precision: int = 15, env: dict = {}):
        super().__init__()
        self.precision = precision
        self.env = env

    def variable(self, name):
        value = self.env.get(name[0].value, name[0])
        if not isinstance(value, Lambda):
            value = tree_repr(value, precision=self.precision, env=self.env)
        else:
            if isinstance(name[0], lark.Token):
                value = lark.Tree("variable", name)  # type: ignore
            else:
                value = lark.Tree("variable", [lark.Token("NAME", name)])  # type: ignore
        return value


def reconstruct(node: Lambda, precision: int = 15, env: dict = {}):
    """
    Reconstruct NumFu source code from a lambda function AST.

    Takes a lambda with its serialized parse tree and closure environment,
    then generates readable NumFu code that represents the function.

    Args:
        node: Lambda function to reconstruct
        precision: Numeric precision for number formatting
        env: Additional environment for variable resolution

    Returns:
        String containing reconstructed NumFu code
    """

    if not node.tree:
        return None
    reconstructor = lark.reconstruct.Reconstructor(
        lark.Lark(grammar, parser="lalr", maybe_placeholders=False)
    )
    tree = pickle.loads(zlib.decompress(node.tree))
    env = {k: v for k, v in node.curry.items() if k not in env}

    tree = Resolver(precision=precision, env=env).transform(tree)
    return reconstructor.reconstruct(tree)
