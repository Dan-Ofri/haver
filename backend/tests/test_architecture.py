"""Guards the plugin architecture: the core must never depend on a domain plugin."""

import ast
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "src" / "haver" / "core"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_core_does_not_import_plugins() -> None:
    offenders = {
        str(path.relative_to(CORE)): sorted(
            n for n in _imports(path) if n.startswith("haver.plugins")
        )
        for path in CORE.rglob("*.py")
    }
    assert {k: v for k, v in offenders.items() if v} == {}
