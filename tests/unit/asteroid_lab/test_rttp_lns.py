"""RTTP local LNS — RTTP-G7 (PR-5)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import django_apps.asteroid_lab.optimization.validation.final_validation as final_validation


def _module_import_names(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[-1] if node.level else node.module.split(".")[-1])
    return names


def test_lns_only_runs_after_commit_failure() -> None:
    """Validation stays read-only; repair lives in commit/LNS modules only."""

    source = inspect.getsource(final_validation)
    assert "local_lns" not in source
    assert "run_local_lns" not in source
    assert "repair" not in source.lower()

    module_file = Path(final_validation.__file__)
    assert module_file is not None
    imported = _module_import_names(module_file)
    repair_modules = {"local_lns", "candidate_generator", "greedy_regret"}
    assert imported.isdisjoint(repair_modules)
    assert "run_local_lns" not in source

    assert "validate_final_layout" in final_validation.__all__
