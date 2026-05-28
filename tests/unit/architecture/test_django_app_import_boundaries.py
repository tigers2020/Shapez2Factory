"""Static import matrix for django_apps (see documents/ai/manuals/django.md)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DJANGO_APPS = _REPO_ROOT / "django_apps"

# source app folder name -> forbidden django_apps.* import prefixes
_FORBIDDEN_IMPORTS: dict[str, frozenset[str]] = {
    "shapez_core": frozenset(
        {
            "django_apps.web",
            "django_apps.shapez_solver",
            "django_apps.asteroid_lab",
            "django_apps.game_data",
        }
    ),
    "shapez_solver": frozenset(
        {
            "django_apps.web",
            "django_apps.asteroid_lab",
            "django_apps.game_data",
        }
    ),
    "asteroid_lab": frozenset(
        {
            "django_apps.web",
            "django_apps.shapez_solver",
            "django_apps.game_data",
        }
    ),
    "game_data": frozenset(
        {
            "django_apps.web",
            "django_apps.shapez_solver",
            "django_apps.asteroid_lab",
        }
    ),
}

# ADR-004: CLI mirrors HTTP — sole snapshot build via web assembler (Track A).
_IMPORT_MATRIX_SKIP: dict[str, frozenset[str]] = {
    "asteroid_lab": frozenset(
        {
            "django_apps/asteroid_lab/management/commands/run_solver.py",
            "django_apps/asteroid_lab/management/commands/scan_rttp_slug_certification.py",
            "django_apps/asteroid_lab/management/commands/capture_rttp_recovery_evidence.py",
            "django_apps/asteroid_lab/services/reconstruction_capacity_summary.py",
            # Lab UI: display-only exterior transport line/connector counts (function-local import).
            "django_apps/asteroid_lab/services/solver_run_lab_summary.py",
            "django_apps/asteroid_lab/services/committed_throughput_summary.py",
            "django_apps/asteroid_lab/services/rttp_exterior_transport_resolver.py",
            # Phase A: display-only sprite resolver reads pinned game_data ORM rows.
            "django_apps/asteroid_lab/catalog/asteroid_sprite_projection.py",
            # ELCP: candidate throughput uses game_data mining rules (function-local import).
            "django_apps/asteroid_lab/optimization/commit/incremental_commit.py",
        }
    ),
}


def _app_py_files(app_name: str) -> list[Path]:
    root = _DJANGO_APPS / app_name
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _imported_django_app_modules(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("django_apps.")
        ):
            found.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("django_apps."):
                    found.add(name)
    return found


def _violations_for_file(path: Path, app_name: str) -> list[str]:
    forbidden = _FORBIDDEN_IMPORTS.get(app_name)
    if not forbidden:
        return []
    rel = path.relative_to(_REPO_ROOT)
    if rel.as_posix() in _IMPORT_MATRIX_SKIP.get(app_name, frozenset()):
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except SyntaxError as exc:
        return [f"{rel}: syntax error {exc}"]
    issues: list[str] = []
    for module in sorted(_imported_django_app_modules(tree)):
        for bad in forbidden:
            if module == bad or module.startswith(f"{bad}."):
                issues.append(f"{rel}: forbidden import {module!r} ({app_name} app)")
                break
    return issues


@pytest.mark.parametrize("app_name", sorted(_FORBIDDEN_IMPORTS))
def test_django_app_import_matrix(app_name: str) -> None:
    violations: list[str] = []
    for path in _app_py_files(app_name):
        violations.extend(_violations_for_file(path, app_name))
    assert violations == [], "\n".join(violations)
