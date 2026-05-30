"""BA-1 core purity gate for ``src/shapez2_factory/**``.

The pure core package MUST NOT import Django, the Django apps, or project settings. This gate is
active and green from PR-CLI-0 onward: it tolerates an empty/scaffold package (only ``__init__.py``
files, no asteroid modules yet) and stays green as real modules land.

Spec: docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md (§8 BA-1)
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_CORE_ROOT = _REPO / "src" / "shapez2_factory"

FORBIDDEN_TOP_LEVEL_PREFIXES = ("django", "django_apps", "config")


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


def test_shapez2_factory_core_root_exists() -> None:
    assert _CORE_ROOT.is_dir(), f"core package root missing: {_CORE_ROOT}"


def test_shapez2_factory_has_no_forbidden_imports() -> None:
    violations: list[str] = []
    for path in _CORE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for module in _imported_modules(tree):
            top = module.split(".")[0]
            if top in FORBIDDEN_TOP_LEVEL_PREFIXES or "django_apps" in module:
                violations.append(f"{path.relative_to(_REPO)} imports {module}")
    assert violations == [], f"core purity (BA-1) violated: {violations}"
