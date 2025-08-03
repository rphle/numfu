import pickle
from pathlib import Path

import click

from .errors import ErrorMeta
from .interpreter import Interpreter
from .parser import Parser
from .repl import REPL


class DefaultGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        cmd = click.Group.get_command(self, ctx, cmd_name)
        if cmd is not None:
            return cmd
        return None

    def resolve_command(self, ctx, args):
        if args and args[0] in self.commands:
            cmd_name = args[0]
            cmd = self.commands[cmd_name]
            return cmd_name, cmd, args[1:]

        if args:
            return "_default", self.commands["_default"], args

        return None, None, []


class ReplGroup(click.Group):
    def resolve_command(self, ctx, args):
        return super().resolve_command(ctx, args)


@click.group(cls=DefaultGroup)
@click.pass_context
def cli(ctx):
    pass


@cli.command(
    name="_default",
    context_settings=dict(ignore_unknown_options=False, allow_interspersed_args=True),
)
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-p",
    "--precision",
    default=15,
    show_default=True,
    type=int,
    help="Floating point precision",
)
@click.option(
    "-r",
    "--rec-depth",
    default=10000,
    show_default=True,
    type=int,
    help="Maximum recursion depth in the evaluation process",
)
@click.option(
    "--curry",
    is_flag=True,
    show_default=True,
    help="Whether to curry",
)
@click.pass_context
def default(ctx, source, precision, rec_depth, curry):
    """Parse and run a NumFu source file."""
    run_file(source, precision, rec_depth, curry)


@cli.command()
@click.argument("source", required=True)
@click.option(
    "-o",
    "--output",
    default="",
    show_default=True,
    type=str,
    help="Output file path",
)
@click.option(
    "--imports",
    default=["builtins"],
    show_default=True,
    type=list,
    help="Names to automatically import",
)
@click.option(
    "--max-depth",
    default=10,
    show_default=True,
    type=int,
    help="Maximum depth of the AST to print",
)
@click.option(
    "--indent",
    default=2,
    show_default=True,
    type=int,
    help="Indentation size for the AST",
)
@click.option(
    "--curry",
    is_flag=True,
    show_default=True,
    help="Whether to curry the AST",
)
def ast(source, output, imports, max_depth, indent, curry):
    """Parse the input file and pretty-print its AST."""
    source_path = Path(source)
    if not source_path.exists() or source_path.is_dir():
        raise click.UsageError(
            f"Invalid or missing source file: {source}\n"
            "For an interactive AST REPL, use: numfu repl ast"
        )
    code = source_path.read_text()
    parser = Parser(errormeta=ErrorMeta(file=source_path, fatal=True), imports=imports)
    repl = REPL(
        imports=imports,
        max_depth=max_depth,
        indent=indent,
    )
    tree, _ = repl.print_ast(parser.parse(code, curry=curry), actually_print=not output)

    if output:
        with open(output, "wb") as f:
            pickle.dump(tree, f)


@cli.group(cls=click.Group, invoke_without_command=True)
@click.option(
    "-p",
    "--precision",
    default=15,
    show_default=True,
    type=int,
    help="Floating point precision",
)
@click.option(
    "-r",
    "--rec-depth",
    default=10000,
    show_default=True,
    type=int,
    help="Maximum recursion depth in the evaluation process",
)
@click.pass_context
def repl(ctx, precision, rec_depth):
    """Start an interactive REPL."""
    if ctx.invoked_subcommand is None:
        # Default to evaluation REPL
        parser = Parser(errormeta=ErrorMeta(fatal=False))
        interpreter = Interpreter(precision, rec_depth)

        def _interpret(code):
            tree = parser.parse(code)
            if tree is None:
                return

            output = interpreter.run(
                tree, ErrorMeta(file="REPL", code=code, fatal=False)
            )

            for o in (o for o in output if o is not None):
                print(o)

        repl_instance = REPL()
        repl_instance.start(_interpret)


@repl.command(name="ast")
@click.option(
    "--max-depth",
    default=10,
    show_default=True,
    type=int,
    help="Maximum depth of the AST to print",
)
@click.option(
    "--indent",
    default=2,
    show_default=True,
    type=int,
    help="Indentation size for the AST",
)
@click.option(
    "--curry",
    is_flag=True,
    show_default=True,
    help="Whether to curry the AST",
)
def repl_ast(max_depth, indent, curry):
    """Start the interactive AST REPL."""
    repl = REPL(max_depth=max_depth, indent=indent)
    parser = Parser(errormeta=ErrorMeta(file="REPL", fatal=False))
    repl.start(
        lambda code: repl.print_ast(parser.parse(code, curry=curry)),
        intro="NumFu AST REPL. Type 'exit' or press Ctrl+D to exit.",
    )


def run_file(source, precision, rec_depth, curry):
    source_path = Path(source)
    code = source_path.read_text()
    errormeta = ErrorMeta(file=source_path, code=code, fatal=True)

    parser = Parser(errormeta)
    tree = parser.parse(code, curry=curry)

    if tree is None:
        return

    output = Interpreter(precision, rec_depth, errormeta=errormeta).run(tree)

    for o in (o for o in output if o is not None):
        print(o)
