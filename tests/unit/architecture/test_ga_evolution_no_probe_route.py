"""PR-GA-1 — GA selection modules must not import route probing."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LAB_ROOT = _REPO_ROOT / "django_apps" / "asteroid_lab"
_GA_FILES = (
    _LAB_ROOT / "optimization" / "selection" / "ga_evolution.py",
    _LAB_ROOT / "optimization" / "selection" / "ga_evolution_shadow.py",
    _LAB_ROOT / "optimization" / "selection" / "genome_fitness.py",
)
_FORBIDDEN = ("probe_route", "route_probe")


def _scan_forbidden(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in _FORBIDDEN):
                    hits.append(f"{path.name}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if any(token in module for token in _FORBIDDEN):
                hits.append(f"{path.name}: from {module}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _FORBIDDEN:
                hits.append(f"{path.name}: call {node.func.id}")
    text = path.read_text(encoding="utf-8-sig")
    for token in _FORBIDDEN:
        if token in text and not any(token in hit for hit in hits):
            if f"import {token}" in text or ("from " in text and token in text):
                hits.append(f"{path.name}: text contains {token!r}")
    return hits


def test_ga_evolution_modules_do_not_import_route_probe() -> None:
    violations: list[str] = []
    for path in _GA_FILES:
        assert path.is_file(), f"missing GA module: {path}"
        violations.extend(_scan_forbidden(path))
    assert violations == []
