"""
Lark-based Parser and AST Generator for NumFu

This module converts NumFu source code into ASTs using the Lark parsing library.
It handles the complete NumFu grammar, most desugaring (like let bindings) is already
done here.
"""

import codecs
import pickle
import re
import zlib
from pathlib import Path

from lark import Lark, Token, Transformer, Tree, v_args

from .ast_types import (
    Bool,
    Call,
    Conditional,
    Constant,
    Delete,
    Export,
    Expr,
    Import,
    Index,
    InlineExport,
    Lambda,
    List,
    Number,
    Pos,
    Spread,
    String,
    Variable,
)
from .classes import Module
from .errors import Error, LarkError, nSyntaxError
from .grammar.grammar import grammar

KEYWORDS = {
    "let",
    "in",
    "if",
    "then",
    "else",
    "import",
    "export",
    "from",
    "del",
    "true",
    "false",
    "$",
    "_",
}


def _tokpos(token: Token):
    return Pos(token.start_pos, token.end_pos)


def _find_tree_end_pos(node):
    return (
        node.children[-1].end_pos
        if isinstance(node.children[-1], Token)
        else _find_tree_end_pos(node.children[-1])
    )


def validate_top_level(tree: Tree) -> Tree | None:
    """
    Verify that certain statements only appear at the top level in the parse tree.
    """

    def traverse(node: Tree | str, top_level: bool = True) -> Tree | None:
        if isinstance(node, Tree):
            for child in node.children:
                if (
                    isinstance(child, Tree)
                    and child.data in ("import_stmt", "export_stmt", "del_stmt")
                    and not top_level
                ):
                    return child
                elif (
                    isinstance(child, Tree)
                    and child.data == "let_binding"
                    and len(child.children) == 3  # no body
                    and not top_level
                ):
                    return child

                if (grandchild := traverse(child, False)) is not None:
                    return grandchild

    return traverse(tree)


def validate_imports(tree: Tree) -> Tree | None:
    """
    Verify that import statements only appear at the top level in the parse tree.
    """
    seen_non_import = False
    for node in tree.children:
        if not (isinstance(node, Tree) and node.data == "import_stmt"):
            seen_non_import = True
        elif seen_non_import:
            return node


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

    def __init__(self, *args, **kwargs) -> None:
        self.invalid: list[dict] = []
        super().__init__(*args, **kwargs)

    def _check_name(self, name: str, label: str, pos: Pos):
        if name in KEYWORDS:
            self.invalid.append(
                {
                    "type": "NameError",
                    "msg": f"{label} cannot be named '{name}'",
                    "pos": pos,
                }
            )

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
        if len(args) == 3:
            left, op, right = args
            return Call(
                Variable(str(op), pos=_tokpos(op)),
                [left, right],
                pos=Pos(left.pos.start, right.pos.end),
            )

        chainable_ops = {"<", "<=", ">", ">="}
        equality_ops = {"==", "!="}

        operators = [str(args[i]) for i in range(1, len(args), 2)]

        all_chainable = all(op in chainable_ops for op in operators)
        all_equality = all(op in equality_ops for op in operators)

        if all_chainable or all_equality:
            left, op, right = args[0], args[1], args[2]
            expr = Call(
                Variable(str(op), pos=_tokpos(op)),
                [left, right],
                pos=Pos(args[0].pos.start, args[-1].pos.end),
            )

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
        else:
            result = Call(
                Variable(str(args[1]), pos=_tokpos(args[1])),
                [args[0], args[2]],
                pos=Pos(args[0].pos.start, args[2].pos.end),
            )

            for i in range(3, len(args), 2):
                op = args[i]
                right = args[i + 1]
                result = Call(
                    Variable(str(op), pos=_tokpos(op)),
                    [result, right],
                    pos=Pos(args[0].pos.start, right.pos.end),
                )

            return result

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

    def lambda_def(self, tree, params, body):
        for param in params.children:
            self._check_name(param.value, "function parameters", _tokpos(param))

        pos = Pos(
            start=(
                _tokpos(params.children[0]).start if params.children else body.pos.start
            ),
            end=body.pos.end + 1,
        )
        arg_names = [str(t.value) for t in params.children]

        return Lambda(
            arg_names,
            body,
            pos=pos,
            tree=bytes.fromhex(tree),
        )

    def let_binding(self, _let, lambda_params, _in=None, body=None):
        """
        Handle let bindings like: let x = 49 in sqrt(x)
        and constant definitions at top level.

        Converts environment definitions into closure calls:
        'let x = 3 in x * x' becomes '{x -> x * x}(3)'
        """
        if body is None:
            if len(lambda_params.children) != 3:
                print(lambda_params)
                self.invalid.append(
                    {
                        "type": "SyntaxError",
                        "msg": "cannot assign multiple identifiers here",
                        "pos": Pos(
                            lambda_params.children[3].start_pos,
                            lambda_params.children[-1].pos.end,
                        ),
                    }
                )
                return
            name, _, value = lambda_params.children
            self._check_name(name.value, "variables", _tokpos(name))
            return Constant(name.value, value, pos=Pos(_let.start_pos, name.end_pos))
        else:
            names, values = lambda_params.children[::3], lambda_params.children[2::3]
            for name in names:
                self._check_name(name.value, "variables", _tokpos(name))

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

    def del_stmt(self, token, name):
        if name.value in ("_", "$"):
            self._check_name(name.value, "variables", _tokpos(name))

        return Delete(name.value, pos=Pos(token.start_pos, name.end_pos))

    def conditional(self, _if, test, _then, then_body, _else, else_body):
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

    def assertion_expr(self, left, cond):
        return Call(
            func=Lambda(
                arg_names=["$"],
                body=Call(
                    func=Variable("assert", pos=cond.pos),
                    args=[cond, left],
                    pos=cond.pos,
                ),
                pos=cond.pos,
            ),
            args=[left],
            pos=cond.pos,
        )

    def import_stmt(self, _import, *args):
        path = args[-1].value[1:-1]
        pattern = re.compile(
            r"^(?![~/])"  # must not start with / or ~
            r"(?:"
            r"[a-zA-Z_][a-zA-Z0-9_]*"  # single name
            r"|(?=.*(?:\.\.|\.|/)).*/[a-zA-Z_][a-zA-Z0-9_]*"  # path with last part as name
            r")$"
        )

        if (
            not pattern.match(path)
            or Path(path).suffix != ""
            or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", Path(path).stem)
            or path.startswith("/")
            or path.startswith("~")
        ):
            self.invalid.append(
                {
                    "type": "NameError",
                    "msg": f"'{path}' is an invalid module name",
                    "pos": _tokpos(args[-1]),
                }
            )

        return Import(
            names=[Variable(a.value, _tokpos(a)) for a in args[:-2]],
            module=path,
            pos=_tokpos(args[-1]),
        )

    def export_stmt(self, _export, *args):
        if len(args) == 3 and isinstance(args[1], Token) and args[1].value == "=":
            name, value = args[0], args[2]
            if name.value in ("_", "$"):
                self._check_name(name.value, "exports", _tokpos(name))

            return InlineExport(
                Variable(name.value, _tokpos(name)),
                value,
                pos=Pos(_export.start_pos, name.end_pos),
            )
        else:
            return Export(
                names=[Variable(a.value, _tokpos(a)) for a in args],
            )


class Parser:
    """
    Main parser class that coordinates the parsing pipeline.

    Converts NumFu source code strings into lists of AST expressions
    that can be executed by the interpreter.

    Args:
        errormeta: Error reporting context
    """

    def __init__(self, fatal: bool = True):
        self.fatal = fatal

        self.parser = Lark(grammar, parser="lalr", maybe_placeholders=False)
        self.lambda_preprocessor = LambdaPreprocessor()
        self.generator = AstGenerator()

    def parse(self, code: str, path: str | Path | None) -> list[Expr] | None:
        self.module = Module(
            path=str(path) if path else "unknown",
            code=zlib.compress(code.encode("utf-8")),
        )

        try:
            parse_tree = self.parser.parse(code)
        except Exception as e:
            LarkError(str(e), self.module, fatal=self.fatal)
            return

        if res := validate_imports(parse_tree):
            nSyntaxError(
                "Imports must be at the top of the file",
                Pos(res.children[0].start_pos, res.children[-1].end_pos),  # type: ignore
                self.module,
                fatal=self.fatal,
            )
            return

        if (res := validate_top_level(parse_tree)) is not None:
            msg = {
                "import_stmt": "Import",
                "export_stmt": "Export",
                "del_stmt": "Delete",
                "let_binding": "Missing 'in' — bare 'let'",
            }[res.data]
            nSyntaxError(
                f"{msg} allowed only at top level",
                Pos(res.children[0].start_pos, _find_tree_end_pos(res)),  # type: ignore
                self.module,
                fatal=self.fatal,
            )
            return

        parse_tree = self.lambda_preprocessor.transform(parse_tree)
        self.generator.invalid.clear()
        ast_tree: list[Expr] = self.generator.transform(parse_tree)

        if self.generator.invalid:
            # We must handle this here because Lark does generally catch all Exceptions in its Transformer
            e = self.generator.invalid[0]
            Error(
                message=e["msg"],
                pos=e["pos"],
                module=self.module,
                name=e.get("type", "SyntaxError"),
                fatal=self.fatal,
            )
            return

        if not isinstance(ast_tree, list):
            ast_tree = [ast_tree]

        index = 0
        while index < len(ast_tree):
            node = ast_tree[index]
            if isinstance(node, InlineExport):
                ast_tree[index] = Constant(node.name.name, node.value, node.pos)
                ast_tree.insert(index + 1, Export([node.name], node.pos))
                ast_tree.insert(index + 2, Delete(node.name.name, node.pos))

            ast_tree[index].pos.index = index  # type: ignore
            if isinstance(node, Constant):
                ast_tree[index].value.pos.index = index  # type: ignore

            index += 1

        return ast_tree
