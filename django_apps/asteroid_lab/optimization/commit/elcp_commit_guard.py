"""Read-only ELCP commit completeness guards for LNS replacement."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneCapacityPlan
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult


def elcp_plan_is_active(exterior_lane_plan: ExteriorLaneCapacityPlan | None) -> bool:
    if exterior_lane_plan is None:
        return False
    return exterior_lane_plan.required_lane_count > 0


def is_elcp_incomplete_commit_result(
    *,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    commit_result: CommitResult,
) -> bool:
    if not elcp_plan_is_active(exterior_lane_plan):
        return False
    if not commit_result.committed_ids:
        return False
    return len(commit_result.exterior_lane_assignments) != len(commit_result.committed_ids)


def retry_may_replace_best(
    *,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    best_result: CommitResult,
    retry_result: CommitResult,
) -> bool:
    if len(retry_result.committed_ids) <= len(best_result.committed_ids):
        return False
    if is_elcp_incomplete_commit_result(
        exterior_lane_plan=exterior_lane_plan,
        commit_result=retry_result,
    ):
        return False
    return True


__all__ = [
    "elcp_plan_is_active",
    "is_elcp_incomplete_commit_result",
    "retry_may_replace_best",
]
