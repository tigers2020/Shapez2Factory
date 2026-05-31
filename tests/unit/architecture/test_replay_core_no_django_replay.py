"""PR-CLI-3b Guard E: core replay emitter must not import Django replay/services/web."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_REPLAY_CORE = _REPO / "src" / "shapez2_factory" / "application" / "asteroid_lab" / "replay_core.py"

_FORBIDDEN_PREFIXES = (
    "django_apps.asteroid_lab.replay",
    "django_apps.asteroid_lab.services",
    "django_apps.web",
)


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


def test_replay_core_does_not_import_django_replay() -> None:
    tree = ast.parse(_REPLAY_CORE.read_text(encoding="utf-8-sig"))
    violations = [
        module
        for module in _imported_modules(tree)
        if any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in _FORBIDDEN_PREFIXES
        )
    ]
    assert violations == []
