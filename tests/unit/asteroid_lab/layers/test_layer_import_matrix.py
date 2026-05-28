"""Import boundary gates for layer stack."""

from __future__ import annotations

import ast
from pathlib import Path


def _iter_import_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
    return modules


def test_reconstruction_does_not_import_layers() -> None:
    root = Path("django_apps/asteroid_lab/reconstruction")
    for path in root.rglob("*.py"):
        for module in _iter_import_modules(path):
            assert "asteroid_lab.layers" not in module, f"{path} imports {module}"


def test_layers_do_not_import_asteroid_lab_optimization() -> None:
    root = Path("django_apps/asteroid_lab/layers")
    forbidden = "django_apps.asteroid_lab.optimization"
    for path in root.rglob("*.py"):
        for module in _iter_import_modules(path):
            assert not module.startswith(forbidden), f"{path} imports {module}"
