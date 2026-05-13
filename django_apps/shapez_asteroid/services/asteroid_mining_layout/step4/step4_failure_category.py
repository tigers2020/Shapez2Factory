"""STEP4 stub-local failure taxonomy (instrumentation-only; not a routing input)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

__all__ = [
    "Step4FailureCategory",
    "blocked_neighbor_counts",
    "build_step4_failure_classification_dict",
    "classify_step4_failure_category",
    "compute_step4_failure_classification",
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
    goal_starvation = "goal_starvation"
    mixed_transport_contamination = "mixed_transport_contamination"
    unknown = "unknown"


def _neighbor_reasons(near: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for entry in near:
        if not isinstance(entry, dict):
            continue
        out.append(str(entry.get("reason") or ""))
    return out


def blocked_neighbor_counts(near: list[dict[str, Any]]) -> dict[str, int]:
    """Count stub-neighbor diagnostic reasons (deterministic key order)."""

    out: dict[str, int] = {}
    for r in _neighbor_reasons(near):
        if not r:
            continue
        out[r] = out.get(r, 0) + 1
    return dict(sorted(out.items()))


def _all_neighbors_hard_protected(near: list[dict[str, Any]]) -> bool:
    rs = _neighbor_reasons(near)
    return bool(rs) and all(r == "hard_protected" for r in rs)


def _all_neighbors_ok(near: list[dict[str, Any]]) -> bool:
    rs = _neighbor_reasons(near)
    return bool(rs) and all(r == "ok" for r in rs)


def _all_stub_exits_blocked_or_unavailable(near: list[dict[str, Any]]) -> bool:
    """T3 stub_isolated: four neighbor diagnostics, each ``blocked`` or ``hard_protected`` only."""

    rs = _neighbor_reasons(near)
    if len(rs) < 4:
        return False
    return all(r in ("blocked", "hard_protected") for r in rs)


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


def _goal_cell_wrong_transport_role(
    goal_cells: frozenset[Coord],
    *,
    cells: dict[Coord, dict[str, Any]],
    want_role: str,
) -> bool:
    """True if any route goal cell carries the opposite transport role (T3 contamination)."""

    for c in goal_cells:
        row = cells.get(c)
        if not row:
            continue
        role = row.get("role")
        if want_role == "belt" and role == "pipe":
            return True
        if want_role == "pipe" and role == "belt":
            return True
    return False


def compute_step4_failure_classification(
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
    goal_cells: frozenset[Coord] | None = None,
    frontier_stop_reason: str | None = None,
    existing_trunk_present: bool = False,
    existing_trunk_goal_count: int = 0,
    reachable_existing_trunk_count: int = 0,
    reachable_exterior_margin_count: int = 0,
    search_budget_exhausted: bool = False,
    expanded_nodes: int | None = None,
    orphan_goal_excluded: bool = False,
) -> tuple[str, str, dict[str, Any]]:
    """Return ``(category, confidence, evidence)`` — deterministic telemetry only."""

    last_err_s = str(last_error or "")
    exhausted = stop_reason == "exhausted" or last_err_s == "no_route_exhausted"
    budget = (
        search_budget_exhausted
        or stop_reason == "budget"
        or last_err_s == "no_route_budget"
        or frontier_stop_reason == "budget"
    )
    frontier_exhausted = frontier_stop_reason == "exhausted" or (
        frontier_stop_reason is None and exhausted
    )

    neighbor_counts = blocked_neighbor_counts(near)
    evidence_core: dict[str, Any] = {
        "route_goal_set_size": int(goal_cells_count),
        "reachable_goal_count": int(reachable_goal_count),
        "frontier_stop_reason": frontier_stop_reason,
        "search_budget_exhausted": bool(budget),
        "blocked_neighbor_counts": dict(neighbor_counts),
        "existing_trunk_goal_count": int(existing_trunk_goal_count),
        "reachable_existing_trunk_count": int(reachable_existing_trunk_count),
        "reachable_exterior_margin_count": int(reachable_exterior_margin_count),
        "expanded_nodes": expanded_nodes,
        "nearest_transport_hops": nearest_transport_hops,
        "existing_trunk_present": bool(existing_trunk_present),
    }

    cat: str = Step4FailureCategory.unknown.value
    conf = "low"

    if budget:
        cat = Step4FailureCategory.search_budget_exhausted.value
        conf = "high"
        return cat, conf, evidence_core

    if goal_cells and _goal_cell_wrong_transport_role(goal_cells, cells=cells, want_role=want_role):
        cat = Step4FailureCategory.mixed_transport_contamination.value
        conf = "medium"
        return cat, conf, evidence_core

    if _all_neighbors_hard_protected(near):
        cat = Step4FailureCategory.protected_corridor_ring.value
        conf = "high"
        return cat, conf, evidence_core

    if orphan_goal_excluded:
        cat = Step4FailureCategory.orphan_merge_forbidden.value
        conf = "medium"
        return cat, conf, evidence_core

    if _all_stub_exits_blocked_or_unavailable(near):
        cat = Step4FailureCategory.stub_isolated.value
        conf = "high"
        return cat, conf, evidence_core

    if nearest_transport_hops is None:
        cat = Step4FailureCategory.no_same_kind_trunk.value
        conf = "medium"
        return cat, conf, evidence_core

    if _wrong_role_transport_adjacent(near, cells=cells, want_role=want_role):
        cat = Step4FailureCategory.orphan_merge_forbidden.value
        conf = "medium"
        return cat, conf, evidence_core

    rs = _neighbor_reasons(near)
    has_blocked = any(r == "blocked" for r in rs)
    has_hard = any(r == "hard_protected" for r in rs)
    bad_non_ok = ("blocked", "step_cost_none", "hard_protected")
    all_bad_non_ok = bool(rs) and all(r in bad_non_ok for r in rs)
    all_step_none = bool(rs) and all(r == "step_cost_none" for r in rs)

    exn = int(expanded_nodes) if isinstance(expanded_nodes, int) else None
    small_expansion = expanded_nodes is None or (
        isinstance(expanded_nodes, int) and expanded_nodes <= 8
    )
    if (
        exhausted
        and small_expansion
        and all_bad_non_ok
        and has_blocked
        and not _all_neighbors_hard_protected(near)
        and not _all_stub_exits_blocked_or_unavailable(near)
    ):
        cat = Step4FailureCategory.geometry_cage.value
        conf = "medium" if exn is not None and exn <= 4 else "low"
        return cat, conf, evidence_core

    if all_step_none and not has_blocked and not has_hard:
        cat = Step4FailureCategory.route_zone_overblocking.value
        conf = "medium"
        return cat, conf, evidence_core

    goals_unreachable = goal_cells_count > 0 and reachable_goal_count == 0
    evidence_core["all_goals_unreachable"] = bool(goals_unreachable)

    if (
        exhausted
        and frontier_exhausted
        and not budget
        and existing_trunk_present
        and existing_trunk_goal_count > 0
        and reachable_existing_trunk_count == 0
        and reachable_exterior_margin_count == 0
        and nearest_transport_hops is not None
    ):
        cat = Step4FailureCategory.merge_starvation.value
        conf = "medium"
        return cat, conf, evidence_core

    if exhausted and goals_unreachable and nearest_transport_hops is not None:
        if _all_neighbors_ok(near):
            cat = Step4FailureCategory.stub_isolated.value
            conf = "high"
            return cat, conf, evidence_core

    if (
        goal_cells_count > 0
        and reachable_goal_count == 0
        and frontier_exhausted
        and not budget
    ):
        cat = Step4FailureCategory.goal_starvation.value
        conf = "medium"
        return cat, conf, evidence_core

    if _stub_neighbor_hard_extras_touch(stub_cell, hard_extras=hard_extras, near=near):
        cat = Step4FailureCategory.protected_corridor_ring.value
        conf = "medium"
        return cat, conf, evidence_core

    cat = Step4FailureCategory.unknown.value
    conf = "low"
    return cat, conf, evidence_core


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
    goal_cells: frozenset[Coord] | None = None,
    frontier_stop_reason: str | None = None,
    existing_trunk_present: bool = False,
    existing_trunk_goal_count: int = 0,
    reachable_existing_trunk_count: int = 0,
    reachable_exterior_margin_count: int = 0,
    search_budget_exhausted: bool = False,
    expanded_nodes: int | None = None,
    orphan_goal_excluded: bool = False,
) -> str:
    """Return a :class:`Step4FailureCategory` value string (telemetry-only)."""

    return compute_step4_failure_classification(
        stop_reason=stop_reason,
        last_error=last_error,
        nearest_transport_hops=nearest_transport_hops,
        near=near,
        goal_cells_count=goal_cells_count,
        reachable_goal_count=reachable_goal_count,
        cells=cells,
        want_role=want_role,
        stub_cell=stub_cell,
        hard_extras=hard_extras,
        goal_cells=goal_cells,
        frontier_stop_reason=frontier_stop_reason,
        existing_trunk_present=existing_trunk_present,
        existing_trunk_goal_count=existing_trunk_goal_count,
        reachable_existing_trunk_count=reachable_existing_trunk_count,
        reachable_exterior_margin_count=reachable_exterior_margin_count,
        search_budget_exhausted=search_budget_exhausted,
        expanded_nodes=expanded_nodes,
        orphan_goal_excluded=orphan_goal_excluded,
    )[0]


def build_step4_failure_classification_dict(
    *,
    category: str,
    confidence: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """T3 NDJSON-stable classification object (category + confidence + evidence)."""

    return {
        "category": str(category),
        "confidence": str(confidence),
        "evidence": dict(evidence),
    }
