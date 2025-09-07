import os
import pickle
import platform
from pathlib import Path
from typing import List, Optional

import click

from ._version import __version__
from .interpreter import Interpreter
from .parser import Parser
from .repl import REPL


class DefaultGroup(click.Group):
    def resolve_command(self, ctx: click.Context, args: List[str]):
        if args and args[0] in self.commands:
            cmd_name = args[0]
            cmd = self.commands[cmd_name]
            return cmd_name, cmd, args[1:]
        if args:
            return "_default", self.commands["_default"], args
        return None, None, []


@click.group(cls=DefaultGroup)
@click.version_option(
    version=__version__,
    prog_name="NumFu",
    message=f"%(prog)s, version %(version)s (Python {platform.python_version()})",
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """CLI tool for the NumFu programmming language."""
    pass


@cli.command(
    name="_default",
    context_settings=dict(ignore_unknown_options=False, allow_interspersed_args=True),
)
@click.argument("source", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option(
    "-p",
    "--precision",
    default=15,
    show_default=True,
    type=int,
    help="Floating point precision for calculations.",
)
@click.option(
    "-r",
    "--rec-depth",
    default=10000,
    show_default=True,
    type=int,
    help="Maximum recursion depth during evaluation.",
)
@click.option(
    "--iter-depth",
    default=-1,
    show_default=True,
    type=int,
    help="Maximum iterations of tail-call optimized recursion during evaluation.",
)
@click.pass_context
def default(
    ctx: click.Context,
    source: str,
    precision: int,
    rec_depth: int,
    iter_depth: int,
) -> None:
    """Parse and run a NumFu source file."""
    run_file(source, precision, rec_depth, iter_depth)


@cli.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option(
    "-p",
    is_flag=True,
    help="Wether to pretty print the AST instead of saving it.",
    default=False,
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Output file path to save the parsed file.",
)
@click.option(
    "-m",
    "--max-depth",
    default=10,
    show_default=True,
    type=int,
    help="Maximum depth of the AST to display.",
)
@click.option(
    "-n",
    "--indent",
    default=2,
    show_default=True,
    type=int,
    help="Indentation size for AST pretty print.",
)
def parse(
    source: str,
    p: bool,
    output: Optional[str],
    max_depth: int,
    indent: int,
) -> None:
    """Parse the input file and serialize or pretty print it"""
    source_path = Path(source)
    code = source_path.read_text()
    parser = Parser(fatal=True)
    repl = REPL(max_depth=max_depth, indent=indent)

    tree, _ = repl.print_ast(parser.parse(code, source_path), actually_print=p)

    if not p:
        if not output:
            output_path = Path(source.removesuffix(".nfu") + ".nfut")
        else:
            output_path = Path(source)
        try:
            output_path.write_bytes(b"NFU-TREE-FILE" + pickle.dumps(tree))
            click.echo(f"Parsed file saved to {output_path}")
        except Exception as e:
            click.echo(f"Error saving parsed file: {e}")


@cli.group(invoke_without_command=True)
@click.option(
    "-p",
    "--precision",
    default=15,
    show_default=True,
    type=int,
    help="Floating point precision used in evaluation.",
)
@click.option(
    "-r",
    "--rec-depth",
    default=10000,
    show_default=True,
    type=int,
    help="Maximum recursion depth during evaluation.",
)
@click.option(
    "--iter-depth",
    default=-1,
    show_default=True,
    type=int,
    help="Maximum iterations of tail-call optimized recursion during evaluation.",
)
@click.pass_context
def repl(
    ctx: click.Context,
    precision: int,
    rec_depth: int,
    iter_depth: int,
) -> None:
    """Start an interactive REPL."""
    if ctx.invoked_subcommand is None:
        parser = Parser(fatal=False)
        interpreter = Interpreter(
            precision,
            rec_depth,
            iter_depth=iter_depth,
            fatal=False,
        )
        env = {}
        modules = {}

        def interpret(code: str) -> None:
            tree = parser.parse(code, path=os.getcwd() + "/")
            if tree is None:
                return

            interpreter.run(
                tree, path=os.getcwd() + "/", code=code, env=env, modules=modules
            )
            env.update(interpreter.modules[interpreter.module_id].globals)
            modules.update(interpreter.modules)

        repl_instance = REPL()
        repl_instance.start(interpret)


@repl.command(name="ast")
@click.option(
    "-m",
    "--max-depth",
    default=10,
    show_default=True,
    type=int,
    help="Maximum depth of the AST to display.",
)
@click.option(
    "-n",
    "--indent",
    default=2,
    show_default=True,
    type=int,
    help="Indentation size for AST pretty print.",
)
def repl_ast(max_depth: int, indent: int) -> None:
    """Start the interactive AST REPL."""
    repl = REPL(max_depth=max_depth, indent=indent)
    parser = Parser(fatal=False)

    def print_ast_repl(code: str):
        tree = parser.parse(code, path=os.getcwd() + "/")
        repl.print_ast(tree)

    repl.start(
        print_ast_repl,
        intro="NumFu AST REPL. Type 'exit' or press Ctrl+D to exit.",
    )


def run_file(source: str, precision: int, rec_depth: int, iter_depth: int) -> None:
    source_path = Path(source)
    parsed = False
    tree = None
    with open(source_path, "rb") as f:
        if f.read(len(b"NFU-TREE-FILE")) == b"NFU-TREE-FILE":
            code = ""
            content = f.read()
            tree = pickle.loads(content) if content else None
            parsed = True
        else:
            try:
                f.seek(0)
                code = f.read().decode("utf-8")
            except UnicodeDecodeError:
                raise click.FileError(source, "unrecognized file format")

    if not parsed:
        parser = Parser(fatal=True)
        tree = parser.parse(code, path=source_path)

    if tree is None:
        return

    interpreter = Interpreter(
        precision,
        rec_depth,
        fatal=True,
        iter_depth=iter_depth,
    )
    interpreter.run(tree, path=source_path, code=code)
