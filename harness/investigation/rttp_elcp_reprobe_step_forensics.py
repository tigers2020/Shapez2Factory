"""Parse algorithm_steps for ELCP reprobe investigation (M2 cross-check)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def extract_elcp_reprobe_forensics(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    commit_metrics: Mapping[str, object] = {}
    for step in algorithm_steps:
        if str(step.get("step_id")) == RttpAlgorithmStepId.RTTP_COMMIT.value:
            metrics = step.get("metrics")
            if isinstance(metrics, Mapping):
                commit_metrics = metrics
            break

    committed_ids = commit_metrics.get("committed_ids")
    committed_count = (
        len(committed_ids)
        if isinstance(committed_ids, Sequence) and not isinstance(committed_ids, str)
        else 0
    )
    conflict_count = commit_metrics.get("conflict_count")
    lane_shortfall = commit_metrics.get("lane_capacity_shortfall_count")
    route_shortfall = commit_metrics.get("route_feasible_shortfall_count")
    elcp_plan = commit_metrics.get("exterior_lane_plan")

    return {
        "committed_count": committed_count,
        "conflict_count": int(conflict_count) if isinstance(conflict_count, int) else None,
        "lane_capacity_shortfall_count": (
            int(lane_shortfall) if isinstance(lane_shortfall, int) else None
        ),
        "route_feasible_shortfall_count": (
            int(route_shortfall) if isinstance(route_shortfall, int) else None
        ),
        "elcp_plan_active": elcp_plan is not None,
        "reprobe_failed_ratio_note": (
            "Per-candidate reprobe histogram requires ledger (M1); "
            "step metrics only expose conflict_count aggregate."
        ),
    }


__all__ = ["extract_elcp_reprobe_forensics"]
