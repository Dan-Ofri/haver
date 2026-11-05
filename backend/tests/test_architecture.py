"""Guards the plugin architecture: the core must never depend on a domain plugin."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
CORE = SRC / "haver" / "core"


def imported_modules(source: str, package: str) -> set[str]:
    """Every module a source file imports, with relative imports resolved against `package`."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = package.split(".")
            base = base[: len(base) - node.level + 1] if node.level else []
            module = ".".join([*base, *([node.module] if node.module else [])])
            names.add(module)
            # `from haver import plugins` imports the sub-module haver.plugins.
            names.update(f"{module}.{alias.name}" for alias in node.names)
    return names


def reaches_plugins(source: str, package: str) -> bool:
    return any(
        name == "haver.plugins" or name.startswith("haver.plugins.")
        for name in imported_modules(source, package)
    )


def test_core_does_not_import_plugins() -> None:
    offenders = []
    for path in CORE.rglob("*.py"):
        parts = path.relative_to(SRC).with_suffix("").parts
        package = ".".join(parts if path.name == "__init__.py" else parts[:-1])
        if reaches_plugins(path.read_text(encoding="utf-8"), package.removesuffix(".__init__")):
            offenders.append(str(path.relative_to(SRC)))
    assert offenders == []


def test_checker_catches_every_import_form() -> None:
    package = "haver.core.agent"
    assert reaches_plugins("import haver.plugins.training", package)
    assert reaches_plugins("from haver.plugins import training", package)
    assert reaches_plugins("from haver import plugins", package)
    assert reaches_plugins("from ...plugins import training", package)
    assert reaches_plugins("from ... import plugins", package)
    assert not reaches_plugins("from haver.core import tools", package)
    assert not reaches_plugins("from . import loop", package)
