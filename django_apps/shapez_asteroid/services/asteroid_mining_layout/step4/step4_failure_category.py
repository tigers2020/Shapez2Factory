"""STEP4 stub-local failure taxonomy (instrumentation-only; not a routing input)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

__all__ = [
    "Step4FailureCategory",
    "build_step4_failure_classification_dict",
    "classify_step4_failure_category",
    "protected_corridor_hard_involved",
]


class Step4FailureCategory(StrEnum):
    """Canonical root-cause labels for STEP4 stub-near routing failures."""

    geometry_cage = "geometry_cage"
    protected_corridor_ring = "protected_corridor_ring"
    merge_starvation = "merge_starvation"
    route_zone_overblocking = "route_zone_overblocking"
    search_budget_exhausted = "search_budget_exhausted"
    no_same_kind_trunk = "no_same_kind_trunk"
    stub_isolated = "stub_isolated"
    orphan_merge_forbidden = "orphan_merge_forbidden"
    unknown = "unknown"


STEP4_FAILURE_CLASSIFICATION_SUBKEYS: tuple[str, ...] = (
    "protected_corridor_hard_involved",
    "all_goals_unreachable",
    "search_budget_exhausted",
    "expanded_nodes",
    "search_time_ms",
    "search_mode",
    "fallback_reason",
    "optimality_guarantee",
)


def _neighbor_reasons(near: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for entry in near:
        if not isinstance(entry, dict):
            continue
        out.append(str(entry.get("reason") or ""))
    return out


def _all_neighbors_hard_protected(near: list[dict[str, Any]]) -> bool:
    rs = _neighbor_reasons(near)
    return bool(rs) and all(r == "hard_protected" for r in rs)


def _all_neighbors_ok(near: list[dict[str, Any]]) -> bool:
    rs = _neighbor_reasons(near)
    return bool(rs) and all(r == "ok" for r in rs)


def _stub_neighbor_hard_extras_touch(
    stub_cell: Coord,
    *,
    hard_extras: frozenset[Coord],
    near: list[dict[str, Any]],
) -> bool:
    if not hard_extras:
        return False
    if stub_cell in hard_extras:
        return True
    for entry in near:
        if not isinstance(entry, dict):
            continue
        cell = entry.get("cell")
        if not isinstance(cell, list) or len(cell) < 2:
            continue
        c = (int(cell[0]), int(cell[1]))
        if c in hard_extras:
            return True
    return False


def _any_neighbor_hard_protected(near: list[dict[str, Any]]) -> bool:
    return any(r == "hard_protected" for r in _neighbor_reasons(near))


def protected_corridor_hard_involved(
    near: list[dict[str, Any]],
    *,
    stub_cell: Coord,
    hard_extras: frozenset[Coord],
) -> bool:
    """True when stub neighborhood intersects hard-protected corridor cells."""

    return _any_neighbor_hard_protected(near) or _stub_neighbor_hard_extras_touch(
        stub_cell, hard_extras=hard_extras, near=near
    )


def _wrong_role_transport_adjacent(
    near: list[dict[str, Any]],
    *,
    cells: dict[Coord, dict[str, Any]],
    want_role: str,
) -> bool:
    """Adjacent opposite belt/pipe role (merge across kind forbidden)."""

    for entry in near:
        if not isinstance(entry, dict):
            continue
        cell = entry.get("cell")
        if not isinstance(cell, list) or len(cell) < 2:
            continue
        c: Coord = (int(cell[0]), int(cell[1]))
        row = cells.get(c)
        if not row:
            continue
        role = row.get("role")
        if want_role == "belt" and role == "pipe":
            return True
        if want_role == "pipe" and role == "belt":
            return True
    return False


def classify_step4_failure_category(
    *,
    stop_reason: str | None,
    last_error: str,
    nearest_transport_hops: int | None,
    near: list[dict[str, Any]],
    goal_cells_count: int,
    reachable_goal_count: int,
    cells: dict[Coord, dict[str, Any]],
    want_role: str,
    stub_cell: Coord,
    hard_extras: frozenset[Coord],
) -> str:
    """Return a :class:`Step4FailureCategory` value string (telemetry-only)."""

    last_err_s = str(last_error or "")
    exhausted = stop_reason == "exhausted" or last_err_s == "no_route_exhausted"
    budget = stop_reason == "budget" or last_err_s == "no_route_budget"

    if budget:
        return Step4FailureCategory.search_budget_exhausted.value
    if _all_neighbors_hard_protected(near):
        return Step4FailureCategory.protected_corridor_ring.value
    if nearest_transport_hops is None:
        return Step4FailureCategory.no_same_kind_trunk.value
    if _wrong_role_transport_adjacent(near, cells=cells, want_role=want_role):
        return Step4FailureCategory.orphan_merge_forbidden.value

    rs = _neighbor_reasons(near)
    has_blocked = any(r == "blocked" for r in rs)
    has_hard = any(r == "hard_protected" for r in rs)
    bad_non_ok = ("blocked", "step_cost_none", "hard_protected")
    all_bad_non_ok = bool(rs) and all(r in bad_non_ok for r in rs)
    all_step_none = bool(rs) and all(r == "step_cost_none" for r in rs)

    if all_bad_non_ok and has_blocked and not _all_neighbors_hard_protected(near):
        return Step4FailureCategory.geometry_cage.value
    if all_step_none and not has_blocked and not has_hard:
        return Step4FailureCategory.route_zone_overblocking.value

    goals_unreachable = goal_cells_count > 0 and reachable_goal_count == 0
    if exhausted and goals_unreachable and nearest_transport_hops is not None:
        if _all_neighbors_ok(near):
            return Step4FailureCategory.stub_isolated.value
        return Step4FailureCategory.merge_starvation.value

    if _stub_neighbor_hard_extras_touch(stub_cell, hard_extras=hard_extras, near=near):
        return Step4FailureCategory.protected_corridor_ring.value

    return Step4FailureCategory.unknown.value


def build_step4_failure_classification_dict(
    *,
    protected_corridor_hard_involved: bool,
    all_goals_unreachable: bool,
    search_budget_exhausted: bool,
    expanded_nodes: int | None,
    search_time_ms: float | None,
    search_mode: str | None,
    fallback_reason: str | None,
    optimality_guarantee: str | None,
) -> dict[str, Any]:
    """Stable insertion order for JSON serialization."""

    values: dict[str, Any] = {
        "protected_corridor_hard_involved": bool(protected_corridor_hard_involved),
        "all_goals_unreachable": bool(all_goals_unreachable),
        "search_budget_exhausted": bool(search_budget_exhausted),
        "expanded_nodes": expanded_nodes,
        "search_time_ms": search_time_ms,
        "search_mode": search_mode,
        "fallback_reason": fallback_reason,
        "optimality_guarantee": optimality_guarantee,
    }
    return {k: values[k] for k in STEP4_FAILURE_CLASSIFICATION_SUBKEYS}
