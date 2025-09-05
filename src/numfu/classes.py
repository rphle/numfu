from dataclasses import dataclass, field, replace
from typing import Any

from .ast_types import (
    Expr,
)


@dataclass
class Module:
    path: str = "unknown"
    code: bytes = field(default_factory=lambda: b"", repr=False)
    id: str = field(default_factory=lambda: "")
    tree: list[Expr] = field(default_factory=lambda: [])
    exports: list[str] = field(default_factory=lambda: [])
    imports: dict[str, str] = field(default_factory=lambda: {})
    globals: dict[str, Any] = field(default_factory=lambda: {})
    depth: int = field(default_factory=lambda: 0)


@dataclass
class State:
    env: dict = field(default_factory=lambda: {})
    module: str = ""
    index: int | None = None

    def edit(self, **kwargs):
        return replace(self, **kwargs)
