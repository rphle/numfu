import importlib.resources
import pickle
import zlib

import lark
import lark.reconstruct
import mpmath

from .ast_types import Lambda, List, Number, String, Variable


def tree_repr(node, env: dict = {}):
    if isinstance(node, (mpmath.mpf, Number)):
        value = lark.Tree(
            "number",
            [
                lark.Token(
                    "NUMBER",  # type: ignore
                    node.value
                    if isinstance(node, Number)
                    else mpmath.nstr(node).removesuffix(".0"),
                )
            ],  # type: ignore
        )
    elif isinstance(node, Lambda):
        value = pickle.loads(zlib.decompress(node.tree))
    elif isinstance(node, Variable):
        value = env.get(node.name, node)
        value = tree_repr(value, env)
    elif isinstance(node, List):
        value = lark.Tree(
            "list_literal",
            [
                lark.Tree(
                    "list_element",
                    [tree_repr(item, env=env | node.curry)],
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
    def __init__(self, env):
        super().__init__()
        self.env = env

    def variable(self, name):
        value = self.env.get(name[0].value, name[0])
        value = tree_repr(value, self.env)
        return value


def reconstruct(node: Lambda, env: dict = {}):
    if not node.tree:
        return None
    grammar = importlib.resources.read_text("numfu", "grammar/numfu.lark")
    reconstructor = lark.reconstruct.Reconstructor(lark.Lark(grammar, parser="lalr"))
    tree = pickle.loads(zlib.decompress(node.tree))
    env = {k: v for k, v in node.curry.items() if k not in env}

    tree = Resolver(env).transform(tree)
    return reconstructor.reconstruct(tree)
