"""Import boundary — projection modules must not enter solver commit internals."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

_FORBIDDEN_IMPORTERS: tuple[Path, ...] = (
    _REPO_ROOT / "django_apps/asteroid_lab/optimization/commit/incremental_commit.py",
    _REPO_ROOT / "django_apps/asteroid_lab/optimization/routing/route_probe.py",
)

_PROJECTION_MODULES: tuple[str, ...] = (
    "django_apps.asteroid_lab.catalog.projection_source",
    "django_apps.asteroid_lab.catalog.asteroid_transport_projection",
    "django_apps.asteroid_lab.catalog.asteroid_equipment_projection",
    "django_apps.asteroid_lab.catalog.asteroid_sprite_projection",
    "django_apps.asteroid_lab.catalog.projection_compat_metrics",
)


def _imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_projection_modules_not_imported_by_solver_commit_internals() -> None:
    violations: list[str] = []
    for path in _FORBIDDEN_IMPORTERS:
        assert path.is_file(), path
        imports = _imports_in_file(path)
        for mod in _PROJECTION_MODULES:
            if mod in imports:
                violations.append(f"{path.name} imports {mod}")
    assert not violations, "; ".join(violations)
