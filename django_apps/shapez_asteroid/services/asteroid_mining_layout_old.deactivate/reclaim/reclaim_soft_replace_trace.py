"""P4 soft-corridor replace trace helpers."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


def p4_soft_replace_neutral_trace(
    *,
    attempted: bool = False,
    committed: bool = False,
    rejected_reason: str | None = None,
    old_cells: list[list[int]] | None = None,
    new_cells: list[list[int]] | None = None,
    connected: bool | None = None,
    job_count: int = 0,
    jobs_attempted: int = 0,
    selected_job_index: int | None = None,
    rejected_reasons_by_job: list[str] | None = None,
    replacement_search_exhausted: bool | None = None,
    replacement_budget_keys: tuple[str, ...] | list[str] | None = None,
    replacement_frontier_last_size: int | None = None,
) -> dict[str, Any]:
    """§14.3 trace keys for soft-corridor atomic replace (no commit / reject / neutral)."""

    out: dict[str, Any] = {
        "p4_soft_replace_attempted": attempted,
        "p4_soft_replace_committed": committed,
        "p4_soft_replace_rejected_reason": rejected_reason,
        "p4_soft_replace_old_cells": list(old_cells or []),
        "p4_soft_replace_new_cells": list(new_cells or []),
        "p4_soft_replace_connected": connected,
        "p4_soft_replace_job_count": job_count,
        "p4_soft_replace_jobs_attempted": jobs_attempted,
        "p4_soft_replace_selected_job_index": selected_job_index,
        "p4_soft_replace_rejected_reasons_by_job": list(rejected_reasons_by_job or []),
    }
    if replacement_search_exhausted is not None:
        out["replacement_search_exhausted"] = replacement_search_exhausted
    if replacement_budget_keys is not None:
        out["replacement_budget_keys"] = list(replacement_budget_keys)
    if replacement_frontier_last_size is not None:
        out["replacement_frontier_last_size"] = int(replacement_frontier_last_size)
    return out


def replacement_probe_path_cardinally_connected(path: list[Coord]) -> bool:
    """Stub-anchor replacement path must be a cardinal polyline (connectivity pre-gate)."""

    if len(path) < 2:
        return False
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        if dx + dy != 1:
            return False
    return True
