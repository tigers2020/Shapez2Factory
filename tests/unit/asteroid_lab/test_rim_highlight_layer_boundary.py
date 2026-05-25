"""Production rim highlight must not import optimization."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
PATHS = [
    REPO / "django_apps" / "asteroid_lab" / "reconstruction" / "rim_highlight.py",
    REPO / "django_apps" / "asteroid_lab" / "services" / "lab_timeline_rim_enrichment.py",
]


@pytest.mark.parametrize("path", PATHS)
def test_no_optimization_import(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "optimization" not in node.module, node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "optimization" not in alias.name, alias.name
