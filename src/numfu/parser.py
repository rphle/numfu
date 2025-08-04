"""
Lark-based Parser and AST Generator for NumFu

This module converts NumFu source code into ASTs using the Lark parsing library.
It handles the complete NumFu grammar, most desugaring (like let bindings) is already
done here.
"""

import codecs
import importlib.resources
import pickle
import re
import zlib

from lark import Lark, Token, Transformer, Tree, v_args

from .ast_types import (
    Assertion,
    Bool,
    Call,
    Conditional,
    Constant,
    Expr,
    Import,
    Index,
    Lambda,
    List,
    Number,
    Spread,
    String,
    Variable,
)
from .errors import ErrorMeta, LarkError, Pos

OPERATORS = [
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
]


def _tokpos(token: Token):
    return Pos(token.start_pos, token.end_pos)


grammar = importlib.resources.read_text("numfu", "grammar/numfu.lark")


@v_args(inline=True)
class LambdaPreprocessor(Transformer):
    def lambda_def(self, *args):
        return Tree(
            "lambda_def",
            [zlib.compress(pickle.dumps(Tree("lambda_def", list(args)))).hex(), *args],
        )


@v_args(inline=True)
class AstGenerator(Transformer):
    """
    Lark transformer that converts parse trees into NumFu AST nodes.

    Each method corresponds to a grammar rule and returns the appropriate
    AST node type. Handles operator precedence, function calls, and
    complex expressions like chained comparisons. Most syntactic sugar is
    already desugared here.
    """

    def start(self, *exprs):
        return list(exprs)

    def bin_op(self, left, op, right):
        return Call(
            Variable(str(op), pos=_tokpos(op)),
            [left, right],
            pos=Pos(left.pos.start, right.pos.end),
        )

    def comp(self, *args):
        """
        Handle chained comparison operators like: a < b <= c > d.

        Converts chains into logical AND expressions:
        a < b <= c becomes (a < b) && (b <= c)
        """

        left, op, right = args[0], args[1], args[2]
        expr = Call(
            Variable(str(op), pos=_tokpos(op)),
            [left, right],
            pos=Pos(args[0].pos.start, args[-1].pos.end),
        )

        if len(args) > 3:
            for i in range(3, len(args), 2):
                left_of_new_link = args[i - 1]
                op = args[i]
                right_of_new_link = args[i + 1]

                next_comp = Call(
                    Variable(str(op), pos=_tokpos(op)),
                    [left_of_new_link, right_of_new_link],
                    pos=_tokpos(op),
                )

                expr = Call(
                    Variable("&&", pos=_tokpos(op)),
                    [expr, next_comp],
                    pos=Pos(args[0].pos.start, args[-1].pos.end),
                )

        return expr

    def pos(self, op, value):
        return value

    def neg(self, op, value):
        return Call(
            Variable(str(op), pos=_tokpos(op)),
            [value],
            pos=Pos(op.start_pos, value.pos.end),
        )

    def not_op(self, op, value):
        return Call(Variable(str(op), pos=_tokpos(op)), [value], pos=_tokpos(op))

    def variable(self, name):
        return Variable(str(name), pos=_tokpos(name))

    def number(self, n):
        return Number(str(n), pos=_tokpos(n))

    def string(self, s):
        return String(codecs.decode(s[1:-1], "unicode_escape"), pos=_tokpos(s))

    def boolean(self, n):
        return Bool(str(n) == "true", pos=_tokpos(n))

    def list_literal(self, *elements):
        if not elements:
            return List([], pos=Pos(0, 0))
        return List(
            list(elements), pos=Pos(elements[0].pos.start - 1, elements[-1].pos.end + 1)
        )

    def rest_param(self, this):
        this.value = "..." + this.value
        return this

    def lambda_def(self, tree, *args):
        name, params, body = (None, *args) if len(args) == 2 else args
        pos = (
            _tokpos(name)
            if name
            else (_tokpos(params.children[0]) if params.children else body.pos)
        )
        arg_names = [str(t.value) for t in params.children]
        return Lambda(
            arg_names,
            body,
            name=str(name) if name else None,
            pos=pos,
            tree=bytes.fromhex(tree),
        )

    def let_binding(self, lambda_params, body):
        """
        Handle let bindings like: let x = 49 in sqrt(x)

        Converts environment definitions into closure calls:
        'let x = 3 in x * x' becomes '{x -> x * x}(3)'
        """
        names, values = lambda_params.children[::2], lambda_params.children[1::2]
        return Call(
            Lambda([str(name) for name in names], body, pos=body.pos),
            values,
            pos=_tokpos(names[0]),
        )

    def list_element(self, value):
        return value

    def spread_op(self, token, value):
        return Spread(value, pos=Pos(token.start_pos, value.pos.end))

    def pipe_chain(self, *args):
        pipes = args[-2::-2]
        chain = [
            Variable(f.value, pos=_tokpos(f)) if isinstance(f, Token) else f
            for f in args[::-2]
        ]

        def construct(i=0):
            return (
                Call(func=chain[i], args=[construct(i + 1)], pos=_tokpos(pipes[i]))
                if i < len(chain) - 1
                else chain[i]
            )

        return construct()

    def compose_chain(self, *args):
        pipes = (args[1],) + args[-2::-2]
        chain = [
            Variable(f.value, pos=_tokpos(f)) if isinstance(f, Token) else f
            for f in args[::-2]
        ]

        def construct_ast(i=0):
            return (
                Call(func=chain[i], args=[construct_ast(i + 1)], pos=_tokpos(pipes[i]))
                if i < len(chain) - 1
                else Call(
                    func=chain[i],
                    args=[Spread(Variable("args", pos=chain[i].pos), pos=chain[i].pos)],
                    pos=chain[i].pos,
                )
            )

        def ast_to_lark_tree(ast_node):
            """Convert an AST node back to its Lark tree representation"""
            if isinstance(ast_node, Variable):
                return Tree("variable", [Token("NAME", ast_node.name)])  # type: ignore
            elif isinstance(ast_node, Call):
                func_tree = ast_to_lark_tree(ast_node.func)
                # Wrap each argument in list_element, except for spread operations
                call_args = []
                for arg in ast_node.args:
                    if isinstance(arg, Spread):
                        call_args.append(ast_to_lark_tree(arg))
                    else:
                        call_args.append(Tree("list_element", [ast_to_lark_tree(arg)]))
                args_tree = Tree("call_args", call_args)
                return Tree("call", [func_tree, args_tree])
            elif isinstance(ast_node, Number):
                return Tree("number", [Token("NUMBER", ast_node.value)])  # type: ignore
            elif isinstance(ast_node, String):
                return Tree("string", [Token("STRING", f'"{ast_node.value}"')])  # type: ignore
            elif isinstance(ast_node, Bool):
                return Tree("boolean", [Token("BOOLEAN", str(ast_node.value).lower())])  # type: ignore
            elif isinstance(ast_node, List):
                return Tree(
                    "list_literal",
                    [
                        Tree("list_element", [ast_to_lark_tree(elem)])
                        for elem in ast_node.elements
                    ],
                )
            elif isinstance(ast_node, Spread):
                return Tree(
                    "spread_op",
                    [Token("SPREAD", "..."), ast_to_lark_tree(ast_node.value)],  # type: ignore
                )
            elif isinstance(ast_node, Lambda):
                return pickle.loads(zlib.decompress(ast_node.tree))
            else:
                raise ValueError(
                    f"Cannot convert AST node {type(ast_node)} to Lark tree"
                )

        def construct_lark_tree(i=0):
            """Recursively build the Lark parse tree for the composition chain"""
            if i < len(chain) - 1:
                func_tree = ast_to_lark_tree(chain[i])
                nested_call = Tree("list_element", [construct_lark_tree(i + 1)])
                return Tree("call", [func_tree, Tree("call_args", [nested_call])])
            else:
                func_tree = ast_to_lark_tree(chain[i])
                spread_arg = Tree(
                    "spread_op",
                    [Token("SPREAD", "..."), Tree("variable", [Token("NAME", "args")])],  # type: ignore
                )
                return Tree("call", [func_tree, Tree("call_args", [spread_arg])])

        lambda_params_tree = Tree(
            "lambda_params",
            [Tree("rest_param", [Token("NAME", "args")])],  # type: ignore
        )

        lambda_tree = Tree("lambda_def", [lambda_params_tree, construct_lark_tree()])

        return Lambda(
            arg_names=["...args"],
            body=construct_ast(),
            tree=zlib.compress(pickle.dumps(lambda_tree)),
            pos=_tokpos(pipes[0]) if pipes else Pos(0, 0),
        )

    def constant_def(self, name, value):
        return Constant(name, value, pos=Pos(name.start_pos - 6, name.end_pos))

    def conditional(self, test, then_body, else_body):
        return Conditional(test, then_body, else_body, pos=test.pos)

    def index_op(self, target, index):
        return Index(target, index, pos=Pos(index.pos.start - 1, index.pos.end + 1))

    def call(self, func, args=None):
        if args is None:
            return func
        return Call(
            func,
            args,
            pos=Pos(
                func.pos.end,
                args[-1].pos.end + 1,
            )
            if args
            else Pos(func.pos.end, func.pos.end + 2),
        )

    def call_args(self, *args):
        return list(args)

    def assertion(self, cond):
        return Assertion(cond, pos=cond.pos)


class Parser:
    """
    Main parser class that coordinates the parsing pipeline.

    Converts NumFu source code strings into lists of AST expressions
    that can be executed by the interpreter.

    Args:
        errormeta: Error reporting context
        imports: List of modules to automatically import
    """

    def __init__(
        self,
        errormeta: ErrorMeta = ErrorMeta(),
        imports: list[str] = ["builtins"],
    ):
        self.parser = Lark(grammar, parser="lalr")
        self.lambda_preprocessor = LambdaPreprocessor()
        self.generator = AstGenerator()
        self.errormeta = errormeta
        self.imports = imports

    def _imports(self, code: str) -> tuple[str, list[Expr]]:
        imports = []
        for i, line in enumerate(
            [f"import {imp}" for imp in self.imports] + code.splitlines()
        ):
            if m := re.search(r"^import\s+(\w+)\s*$", line):
                imports.append(Import(m.group(1)))
            else:
                code = "\n".join(code.splitlines()[max(i - len(self.imports), 0) :])
                break
        return code, imports

    def parse(self, code: str, errormeta: ErrorMeta | None = None) -> list[Expr] | None:
        code, imports = self._imports(code)
        self.errormeta = errormeta or self.errormeta
        self.errormeta.code = code
        try:
            parse_tree = self.parser.parse(code)
            parse_tree = self.lambda_preprocessor.transform(parse_tree)
            ast_tree = self.generator.transform(parse_tree)
            if not isinstance(ast_tree, list):
                ast_tree = [ast_tree]

            tree = []
            for i, stmt in enumerate(ast_tree):
                if isinstance(stmt, Assertion):
                    tree[-1] = Call(
                        func=Lambda(
                            arg_names=["_"],
                            body=Call(
                                func=Variable("assert", pos=stmt.pos),
                                args=[stmt.test, tree[-1]],
                                pos=stmt.pos,
                            ),
                            pos=stmt.test.pos,  # type:ignore
                        ),
                        args=[tree[-1]],
                        pos=stmt.test.pos,  # type:ignore
                    )
                else:
                    tree.append(stmt)

        except Exception as e:
            LarkError(str(e), self.errormeta)
            return None

        tree = imports + tree
        return tree
