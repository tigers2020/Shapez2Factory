"""Resolve repo doc paths after documents/knowledge migration (CI baseline)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

_CURRENT_PLAN_CANDIDATES: tuple[str, ...] = (
    "documents/ai/current_plan.md",
    "documents/knowledge/raw/ai/current_plan.md",
)

_SIMULATION_PRIORITY_AUDIT_CANDIDATES: tuple[str, ...] = (
    "documents/game_data_analysis/simulation_systems/_nested_path_audit_priority.tsv",
    "documents/knowledge/raw/analysis/simulation_systems/_nested_path_audit_priority.tsv",
)


def _resolve_first(candidates: tuple[str, ...]) -> Path | None:
    for relative in candidates:
        path = _REPO_ROOT / relative
        if path.is_file():
            return path
    return None


def resolve_current_plan_path() -> Path | None:
    return _resolve_first(_CURRENT_PLAN_CANDIDATES)


def resolve_simulation_priority_audit_tsv() -> Path | None:
    return _resolve_first(_SIMULATION_PRIORITY_AUDIT_CANDIDATES)


__all__ = ["resolve_current_plan_path", "resolve_simulation_priority_audit_tsv"]
