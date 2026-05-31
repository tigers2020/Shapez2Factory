"""SolverRun artifact fields remain Django-side cache/index metadata."""

from __future__ import annotations

import ast
from pathlib import Path

from django_apps.asteroid_lab.models import SolverRun


def test_solver_run_artifact_fields_document_cache_contract() -> None:
    artifact_root = SolverRun._meta.get_field("artifact_root")
    lifecycle_status = SolverRun._meta.get_field("lifecycle_status")

    assert "cache/index only" in str(artifact_root.help_text)
    assert "not solver input" in str(artifact_root.help_text)
    assert "artifact/index state" in str(lifecycle_status.help_text)
    assert "manifest remains artifact authority" in str(lifecycle_status.help_text)


def test_core_package_does_not_create_solver_run() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "shapez2_factory"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported_names = {alias.name for alias in node.names}
                if "create_solver_run" in imported_names:
                    offenders.append(str(path.relative_to(root)))
            elif isinstance(node, ast.Call):
                call = node.func
                if isinstance(call, ast.Name) and call.id == "create_solver_run":
                    offenders.append(str(path.relative_to(root)))
                if isinstance(call, ast.Attribute) and call.attr == "create_solver_run":
                    offenders.append(str(path.relative_to(root)))

    assert offenders == []
