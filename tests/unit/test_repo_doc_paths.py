"""Repo doc path resolution after knowledge migration."""

from __future__ import annotations

from tests.support.repo_doc_paths import (
    resolve_current_plan_path,
    resolve_simulation_priority_audit_tsv,
)


def test_resolve_current_plan_path_finds_tracked_file() -> None:
    path = resolve_current_plan_path()
    assert path is not None
    assert path.name == "current_plan.md"


def test_resolve_simulation_priority_audit_tsv_finds_tracked_file() -> None:
    path = resolve_simulation_priority_audit_tsv()
    assert path is not None
    assert path.name == "_nested_path_audit_priority.tsv"
