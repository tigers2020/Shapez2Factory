"""AST import boundaries for coordinate frame migration (PR-A)."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_OPTIMIZATION = _REPO / "django_apps" / "asteroid_lab" / "optimization"


def test_optimization_does_not_import_server_xy_for_raw_xy() -> None:
    """Algorithm layer must not call deprecated raw→server bridge directly."""

    if not _OPTIMIZATION.is_dir():
        return

    violations: list[str] = []
    for path in sorted(_OPTIMIZATION.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if "server_coords" not in node.module:
                continue
            for alias in node.names:
                if alias.name == "server_xy_for_raw_xy":
                    violations.append(f"{path.relative_to(_REPO)}:{node.lineno}")
    assert not violations, "server_xy_for_raw_xy in optimization: " + ", ".join(violations)
