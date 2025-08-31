import hashlib
import importlib.resources
import itertools
import pickle
import zlib
from functools import lru_cache
from pathlib import Path

from .ast_types import Constant, Export, Expr, Import, Lambda, Variable
from .classes import Module
from .errors import nImportError
from .parser import Parser


@lru_cache()
def _id(path: str | Path):
    return hashlib.md5(str(path).encode()).hexdigest()


class ImportResolver:
    def __init__(
        self,
        builtins: bool = True,
    ):
        self.precedence = (
            self.file,
            self.stdlib,
        )
        self.modules: dict[str, Module] = {}

        self.builtins = builtins

        self.parser = Parser()

    def stdlib(self, node):
        path = f"stdlib/{node.module}.nfut"
        if _id(path) in self.modules:
            return path

        if importlib.resources.files("numfu").joinpath(path).is_file():
            tree = pickle.loads(
                importlib.resources.read_binary("numfu", path)[len(b"NFU-TREE-FILE") :]
            )
            self._module(path=path, tree=tree, code="", builtins=False)
            return path

    def file(self, node):
        path = (
            (
                (
                    Path(self.path).parent
                    if not self.path.endswith("/")
                    else Path(self.path)
                )
                / Path(node.module + ".nfu")
            )
            .resolve()
            .absolute()
        )
        if _id(path) in self.modules:
            return path
        if not path.is_file():
            return

        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        tree = self._parse(code, node.module)
        self._module(path, tree, code)  # type: ignore
        return path

    def _module(self, path: str, tree: list[Expr], code: str, builtins: bool = True):
        imports = (
            {
                e: "stdlib/builtins.nfut"
                for e in self.modules[_id("stdlib/builtins.nfut")].exports
            }
            if builtins
            else {}
        )

        import_paths = self._resolve(tree, path=path, code=code)
        for _import, _path in zip(
            [i for i in tree if isinstance(i, Import)],
            import_paths,
        ):
            if len(_import.names) > 0:
                if _import.names[0].name == "*":
                    imports.update(
                        {name: _id(_path) for name in self.modules[_id(_path)].exports}
                    )
                else:
                    imports.update({name.name: _id(_path) for name in _import.names})
            else:
                prefix = Path(_path).stem
                imports.update(
                    {
                        f"{prefix}.{name}": _id(_path)
                        for name in self.modules[_id(_path)].exports
                    }
                )

        self.modules[_id(path)] = Module(
            path=str(path),
            code=zlib.compress(code.encode()),
            id=_id(path),
            tree=[
                expr
                for expr in tree
                if isinstance(expr, (Lambda, Constant)) and expr.name
            ],
            exports=list(
                itertools.chain.from_iterable(
                    [[n.name for n in e.names] for e in tree if isinstance(e, Export)]
                )
            )
            if tree
            else [],
            imports=imports,
        )

    def _parse(self, code: str, path: str):
        return self.parser.parse(code, path=path)

    def _resolve(self, tree: list[Expr | Import], path: str, code: str) -> list[str]:
        paths = []
        for node in tree:
            if isinstance(node, Import):
                try:
                    paths.append(
                        str(
                            next(
                                r for f in self.precedence if (r := f(node)) is not None
                            )
                        )
                    )
                except StopIteration:
                    nImportError(
                        f'Cannot find module "{node.module}"',
                        node.pos,
                        module=Module(
                            path=path, code=zlib.compress(code.encode("utf-8"))
                        ),
                    )
            else:
                break

        return paths

    def resolve(
        self, tree: list[Expr | Import], path: str, code: str
    ) -> dict[str, Module]:
        self.path: str = path
        self.stdlib(Import(names=[Variable(name="*")], module="builtins"))
        self._module(path=self.path, tree=tree, code=code, builtins=self.builtins)
        print(self.modules)
        return self.modules
