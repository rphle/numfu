import hashlib
import importlib.resources
import itertools
import pickle
import zlib
from functools import lru_cache
from pathlib import Path

from .ast_types import Constant, Export, Expr, Import, Variable
from .builtins import Io, Math, Random, Std, System, Types
from .classes import Module
from .errors import Pos, nImportError
from .parser import Parser


@lru_cache()
def _id(path: str | Path):
    return hashlib.md5(str(path).encode()).hexdigest()


class ImportResolver:
    def __init__(
        self,
    ):
        self.precedence = (
            self.file,
            self.folder,
            self.stdlib,
        )
        self.modules: dict[str, Module] = {}
        self.parser = Parser()
        self._import_stack: list[str] = []

    def stdlib(self, node):
        if _id(node.module) in self.modules:
            return node.module

        modules = {
            "builtins": {"builtins": None, "file": True},
            "math": {"builtins": Math, "file": False},
            "std": {"builtins": Std, "file": False},
            "io": {"builtins": Io, "file": False},
            "sys": {"builtins": System, "file": False},
            "random": {"builtins": Random, "file": False},
            "types": {"builtins": Types, "file": False},
        }
        if module := modules.get(node.module):
            tree: list[Import | Constant | Export] = []
            if module["builtins"] is not None:
                available = {
                    name: v
                    for name, v in module["builtins"].__dict__.items()
                    if not name.startswith("__")
                }
                tree = [
                    Constant(name=getattr(v, "name", name), value=v, pos=Pos(index=-1))
                    for name, v in available.items()
                ]
                tree.append(
                    Export(
                        names=[
                            Variable(getattr(v, "name", name))
                            for name, v in available.items()
                        ]
                    )
                )
            if module["file"]:
                # Allows importing files from the built-in standard library written in NumFu itself.
                path = f"{node.module}.nfut"

                if importlib.resources.files("numfu.stdlib").joinpath(path).is_file():
                    tree.extend(
                        pickle.loads(
                            importlib.resources.read_binary("numfu.stdlib", path)[
                                len(b"NFU-TREE-FILE") :
                            ]
                        )
                    )

            self._module(path=node.module, tree=tree, code="", builtins=False)  # type: ignore
            return node.module

    def folder(self, node):
        """
        Allows importing a folder by name if it contains an index.nfu file.
        """
        folder_path = (
            (
                (
                    Path(self.path).parent
                    if not self.path.endswith("/")
                    else Path(self.path)
                )
                / Path(node.module)
            )
            .resolve()
            .absolute()
        )

        if not folder_path.is_dir():
            return

        index_path = folder_path / "index.nfu"
        if not index_path.is_file():
            return

        if _id(index_path) in self.modules:
            return index_path

        # Check for circular import
        index_path_str = str(index_path)
        if index_path_str in self._import_stack:
            cycle = self._import_stack[self._import_stack.index(index_path_str) :] + [
                index_path_str
            ]
            cycle_str = " -> ".join(f"'{p}'" for p in cycle)
            nImportError(
                f"Circular import detected:\n{cycle_str}",
                module=Module(
                    path=self.path,
                    code=zlib.compress(self.current_code.encode("utf-8")),
                    depth=len(self._import_stack),
                ),
            )

        self._import_stack.append(index_path_str)
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = self._parse(code, node.module)
            self._module(index_path, tree, code)  # type: ignore
            return index_path
        finally:
            self._import_stack.pop()

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

        # Check for circular import
        path_str = str(path)
        if path_str in self._import_stack:
            cycle = self._import_stack[self._import_stack.index(path_str) :] + [
                path_str
            ]
            cycle_str = " -> ".join(f"'{p}'" for p in cycle)
            nImportError(
                f"Circular import detected:\n{cycle_str}",
                module=Module(
                    path=self.path,
                    code=zlib.compress(self.current_code.encode("utf-8")),
                    depth=len(self._import_stack),
                ),
            )

        self._import_stack.append(path_str)
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = self._parse(code, node.module)
            self._module(path, tree, code)  # type: ignore
            return path
        finally:
            self._import_stack.pop()

    def _module(self, path: str, tree: list[Expr], code: str, builtins: bool = True):
        imports = (
            {e: "builtins" for e in self.modules[_id("builtins")].exports}
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
                    imported_names = set(
                        n.name
                        for n in _import.names
                        if n and hasattr(n, "name") and n.name
                    )
                    exported_names = set(self.modules[_id(_path)].exports)

                    if unknown := (imported_names - exported_names):
                        # find the first import name that's in the unknown set
                        unknown_import = next(
                            (n for n in _import.names if n.name in unknown), None
                        )

                        if len(exported_names):
                            suggestion = f" Available exports are: {', '.join(sorted(exported_names))}"
                        else:
                            suggestion = " This module does not export anything."

                        nImportError(
                            f"Module '{_import.module}' does not export an identifier named '{list(unknown)[0]}'.{suggestion}",
                            unknown_import.pos if unknown_import else None,
                            module=Module(
                                path=str(path),
                                code=zlib.compress(code.encode("utf-8")),
                                depth=len(self._import_stack),
                            ),
                        )
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
                if (isinstance(expr, Constant) and expr.name)
                or isinstance(expr, (Import, Export))
            ],
            exports=list(
                itertools.chain.from_iterable(
                    [[n.name for n in e.names] for e in tree if isinstance(e, Export)]
                )
            )
            if tree
            else [],
            imports=imports,
            depth=len(self._import_stack),
        )

    def _parse(self, code: str, path: str):
        return self.parser.parse(code, path=path)

    def _resolve(self, tree: list[Expr | Import], path: str, code: str) -> list[str]:
        paths = []
        for node in tree:
            if isinstance(node, Import):
                try:
                    original_path = self.path
                    self.path = str(path)

                    resolved_path = next(
                        r for f in self.precedence if (r := f(node)) is not None
                    )
                    paths.append(str(resolved_path))

                    if original_path is not None:
                        self.path = original_path

                except StopIteration:
                    nImportError(
                        f'Cannot find module "{node.module}"',
                        node.pos,
                        module=Module(
                            path=str(path),
                            code=zlib.compress(code.encode("utf-8")),
                            depth=len(self._import_stack),
                        ),
                    )
            else:
                break

        return paths

    def resolve(
        self, tree: list[Expr | Import], path: str, code: str
    ) -> dict[str, Module]:
        self.path: str = path
        self.current_code: str = code

        self.stdlib(Import(names=[Variable(name="*")], module="builtins"))
        self._module(path=self.path, tree=tree, code=code, builtins=True)

        return self.modules
