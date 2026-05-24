"""Track B2: optimization must not import building geometry snapshot types."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_OPTIMIZATION_ROOT = _REPO_ROOT / "django_apps" / "asteroid_lab" / "optimization"

_FORBIDDEN_SYMBOLS = frozenset(
    {
        "BuildingFootprintCell",
        "BuildingConnectorSnapshot",
        "BuildingSnapshot",
    }
)


def _forbidden_imports_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    rel = path.relative_to(_REPO_ROOT)
    issues: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "django_apps.asteroid_lab.contracts.game_data_snapshot":
            continue
        for alias in node.names:
            if alias.name in _FORBIDDEN_SYMBOLS:
                issues.append(f"{rel}: imports {alias.name} from game_data_snapshot")
    return issues


def test_optimization_modules_do_not_import_building_geometry_types() -> None:
    violations: list[str] = []
    for path in sorted(_OPTIMIZATION_ROOT.rglob("*.py")):
        violations.extend(_forbidden_imports_in_file(path))
    assert violations == []
