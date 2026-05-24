"""Track D+ PR-3 — arch gate: production generator must not use lin_* library."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_GENERATOR = (
    _REPO
    / "django_apps"
    / "asteroid_lab"
    / "optimization"
    / "candidates"
    / "candidate_generator.py"
)


def test_candidate_generator_does_not_reference_build_pattern_library() -> None:
    tree = ast.parse(_GENERATOR.read_text(encoding="utf-8-sig"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        if isinstance(node, ast.ImportFrom) and node.module:
            if "pattern_library" in node.module:
                raise AssertionError(f"imports pattern_library: {node.module}")
    assert "build_pattern_library" not in names
