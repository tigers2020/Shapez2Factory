"""§12.6 reclaim loop after Pass3."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_RECLAIM_ITERATIONS,
    MAX_RECLAIM_SHADOW_SCAN_LIMIT,
    P4_REJECT_NO_SHADOW_CANDIDATE,
    P4_REJECT_SOFT_PROTECTED_CORRIDOR,
    P4_SOFT_REPLACE_V2_CONTRACT,
    RECLAIM_CONTINUITY_MULTI_WINDOW_ENABLED,
    RECLAIM_CONTINUITY_WINDOW,
    RECLAIM_DIVERSITY_NEAR_RADIUS,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_p4_bundle import (
    select_best_accepted_p4_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_route_metrics import (  # noqa: E501
    _p4_incremental_route_coords_from_commit_trace,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_soft_replace import (  # noqa: E501
    _p4_soft_replace_neutral_trace,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_context import (
    RECOVERY_SEGMENT_P4_RECLAIM,
    RECOVERY_SEGMENT_SOFT_REPLACE_V2,
    extend_recovery_chain,
)

from .reclaim_shadow_commit_trace import p4_reclaim_provisional_commit_neutral_trace


def _p4_extractor_coords_across_commits(acc_ex: list[list[int]]) -> list[Coord]:
    out: list[Coord] = []
    for cell in acc_ex:
        if isinstance(cell, (list, tuple)) and len(cell) == 2:
            xa, ya = cell[0], cell[1]
            if isinstance(xa, int) and isinstance(ya, int) and xa != 0:
                out.append((xa, ya))
    return out


def _p4_recent_reclaim_window_newest_first(
    acc_ex: list[list[int]],
    *,
    max_window: int,
) -> tuple[Coord, ...] | None:
    coords = _p4_extractor_coords_across_commits(acc_ex)
    if not coords:
        return None
    tail = coords[-max_window:]
    return tuple(reversed(tail))


def _p4_frontier_orbit_streak_consecutive(acc_ex: list[list[int]], *, radius: int) -> int:
    """Trailing commits whose anchor stays within ``radius`` (Manhattan) of the previous.

    Snapshot **before** the next P4-A scan; emitted as ``p4_reclaim_frontier_orbit_streak_prior``
    and copied into best-candidate ``p4_diversity.frontier_orbit_score`` for NDJSON diagnostics.
    """
    coords = _p4_extractor_coords_across_commits(acc_ex)
    if len(coords) < 2:
        return len(coords)
    streak = 1
    for j in range(len(coords) - 1, 0, -1):
        a, b = coords[j], coords[j - 1]
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) <= radius:
            streak += 1
        else:
            break
    return streak


def run_p4_reclaim_loop_after_pass3(
    map_before_pass3: list[dict[str, Any]],
    map_after_pass3_initial: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    pass3_trace: dict[str, Any],
    solver_routing_state: Mapping[str, object] | None,
    is_external: Callable[[Coord], bool],
    p4_reclaim_provisional_commit_enabled: bool = True,
    p4_reclaim_incremental_route_commit_enabled: bool = True,
    max_loop_iterations: int = MAX_RECLAIM_ITERATIONS,
    existing_layout_solver_hints: Mapping[str, object] | None = None,
    p4_baseline_internal_transport_at_reclaim_entry: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """§12.6 reclaim loop: rescan after each commit; cumulative internal-transport spend (§12.2).

    ``p4_reclaim_route_zone_excluded_cumulative_count`` / ``p4_reclaim_last_*`` are solver-summary
    snapshots (latest B2 path); authoritative replay detail remains in merged trace fields.

    §14.3 soft replace: ``p4_soft_replace_attempt_count`` / ``p4_soft_replace_commit_count`` are
    loop-cumulative; ``p4_soft_replace_attempted`` / ``p4_soft_replace_committed`` / cell lists
    reflect the **last** replace call only (corridor repair vs reclaim commit are separate).
    """

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow as _p4f  # noqa: E501

    spent = 0
    commits = 0
    map_cur = map_after_pass3_initial
    acc_ex: list[list[int]] = []
    acc_ext: list[list[int]] = []
    acc_stub: list[list[int]] = []
    acc_route_zone: set[Coord] = set()
    merged: dict[str, Any] = {
        "p4_reclaim_loop_max_iterations": max_loop_iterations,
        "p4_reclaim_shadow_scan_limit": MAX_RECLAIM_SHADOW_SCAN_LIMIT,
        "p4_reclaim_loop_iterations_executed": 0,
        "p4_reclaim_loop_successful_commits": 0,
        "p4_reclaim_loop_internal_transport_cumulative_added": 0,
        "p4_reclaim_loop_terminated_reason": None,
        "p4_reclaim_route_zone_excluded_cumulative_count": 0,
        "p4_reclaim_last_commit_route_cells": [],
        "p4_reclaim_last_soft_protected_candidate_cells": [],
        **_p4_soft_replace_neutral_trace(),
        "p4_soft_replace_contract": None,
        "p4_soft_replace_attempt_count": 0,
        "p4_soft_replace_commit_count": 0,
        "recovery_context_chain": [],
    }
    extend_recovery_chain(merged, RECOVERY_SEGMENT_P4_RECLAIM)

    for i in range(max_loop_iterations):
        prior_anchor_cells: frozenset[Coord] = frozenset()
        if acc_ex:
            ps: set[Coord] = set()
            for cell in acc_ex:
                if isinstance(cell, (list, tuple)) and len(cell) == 2:
                    xa, ya = cell[0], cell[1]
                    if isinstance(xa, int) and isinstance(ya, int) and xa != 0:
                        ps.add((xa, ya))
            prior_anchor_cells = frozenset(ps)

        continuity_window = (
            RECLAIM_CONTINUITY_WINDOW if RECLAIM_CONTINUITY_MULTI_WINDOW_ENABLED else 1
        )
        p4_recent_reclaim_anchors = _p4_recent_reclaim_window_newest_first(
            acc_ex,
            max_window=continuity_window,
        )
        p4_last_reclaim_anchor = p4_recent_reclaim_anchors[0] if p4_recent_reclaim_anchors else None

        orbit_prior = _p4_frontier_orbit_streak_consecutive(
            acc_ex,
            radius=RECLAIM_DIVERSITY_NEAR_RADIUS,
        )

        scan = _p4f.reclaim_shadow_scan_core_after_pass3(
            map_before_pass3,
            map_cur,
            final_mining_map=final_mining_map,
            is_external=is_external,
            pass3_trace=pass3_trace,
            solver_routing_state=solver_routing_state,
            existing_layout_solver_hints=existing_layout_solver_hints,
            reclaim_internal_transport_spent_prior=spent,
            p4_committed_route_cells_for_zone=frozenset(acc_route_zone) if acc_route_zone else None,
            p4_prior_reclaim_anchors=prior_anchor_cells if prior_anchor_cells else None,
            p4_last_reclaim_anchor=p4_last_reclaim_anchor,
            p4_recent_reclaim_anchors=p4_recent_reclaim_anchors,
            p4_frontier_orbit_streak_prior=orbit_prior,
            p4_baseline_internal_transport_at_reclaim_entry=p4_baseline_internal_transport_at_reclaim_entry,
            p4_compare_baseline_internal_to_scan_entry=(i == 0),
        )
        merged.update(scan.trace)
        merged["p4_reclaim_loop_iterations_executed"] = i + 1

        if not scan.trace.get("p4_reclaim_shadow_enabled"):
            merged["p4_reclaim_loop_successful_commits"] = commits
            merged["p4_reclaim_loop_internal_transport_cumulative_added"] = spent
            merged["p4_reclaim_loop_terminated_reason"] = str(
                scan.trace.get("p4_reclaim_shadow_skip_reason") or "p4_shadow_disabled"
            )
            if commits:
                merged["p4_reclaim_added_extractor_cells"] = acc_ex
                merged["p4_reclaim_added_extension_cells"] = acc_ext
                merged["p4_reclaim_added_stub_cells"] = acc_stub
            elif not merged.get("p4_reclaim_provisional_commit_attempted", False):
                _sr = scan.trace.get("p4_reclaim_shadow_skip_reason") or "p4_shadow_disabled"
                merged.update(
                    p4_reclaim_provisional_commit_neutral_trace(
                        attempted=False,
                        skip_reason=str(_sr),
                    )
                )
            return map_cur, merged

        sr = scan.trace.get("p4_reclaim_shadow_skip_reason")
        if sr:
            merged["p4_reclaim_loop_successful_commits"] = commits
            merged["p4_reclaim_loop_internal_transport_cumulative_added"] = spent
            merged["p4_reclaim_loop_terminated_reason"] = str(sr)
            if commits:
                merged["p4_reclaim_added_extractor_cells"] = acc_ex
                merged["p4_reclaim_added_extension_cells"] = acc_ext
                merged["p4_reclaim_added_stub_cells"] = acc_stub
            elif not merged.get("p4_reclaim_provisional_commit_attempted", False):
                merged.update(
                    p4_reclaim_provisional_commit_neutral_trace(
                        attempted=False,
                        skip_reason=str(sr),
                    )
                )
            return map_cur, merged

        picked = select_best_accepted_p4_bundle(scan.evals)
        if picked is None or scan.transport_kind is None:
            merged["p4_reclaim_loop_successful_commits"] = commits
            merged["p4_reclaim_loop_internal_transport_cumulative_added"] = spent
            merged["p4_reclaim_loop_terminated_reason"] = (
                "no_accepted_shadow" if picked is None else "no_transport_kind"
            )
            if commits:
                merged["p4_reclaim_added_extractor_cells"] = acc_ex
                merged["p4_reclaim_added_extension_cells"] = acc_ext
                merged["p4_reclaim_added_stub_cells"] = acc_stub
            else:
                merged.update(
                    p4_reclaim_provisional_commit_neutral_trace(
                        attempted=True,
                        rollback_reason=P4_REJECT_NO_SHADOW_CANDIDATE,
                    )
                )
            return map_cur, merged

        map_next, commit_tr = _p4f.run_p4_reclaim_provisional_commit_after_pass3(
            map_cur,
            final_mining_map=final_mining_map,
            pass3_trace=pass3_trace,
            solver_routing_state=solver_routing_state,
            scan_result=scan,
            p4_reclaim_provisional_commit_enabled=p4_reclaim_provisional_commit_enabled,
            is_external=is_external,
            p4_reclaim_incremental_route_commit_enabled=p4_reclaim_incremental_route_commit_enabled,
            existing_layout_solver_hints=existing_layout_solver_hints,
            reclaim_internal_transport_spent_prior=spent,
        )
        ct = dict(commit_tr)
        ae = ct.pop("p4_reclaim_added_extractor_cells", None)
        aext = ct.pop("p4_reclaim_added_extension_cells", None)
        ast = ct.pop("p4_reclaim_added_stub_cells", None)
        merged.update(ct)
        if ae:
            acc_ex.extend(ae)
        if aext:
            acc_ext.extend(aext)
        if ast:
            acc_stub.extend(ast)

        if not commit_tr.get("p4_reclaim_provisional_commit_committed"):
            rr = commit_tr.get("p4_reclaim_provisional_commit_rollback_reason")
            coll = commit_tr.get("p4_reclaim_soft_corridor_transport_collision_cells")
            if rr == P4_REJECT_SOFT_PROTECTED_CORRIDOR and isinstance(coll, list) and coll:
                merged["p4_soft_replace_contract"] = P4_SOFT_REPLACE_V2_CONTRACT
                old_cells: list[Coord] = []
                for xy in coll:
                    if isinstance(xy, (list, tuple)) and len(xy) == 2:
                        x, y = xy[0], xy[1]
                        if isinstance(x, int) and isinstance(y, int) and x != 0:
                            old_cells.append((x, y))
                if old_cells:
                    merged["p4_soft_replace_attempt_count"] = (
                        int(merged.get("p4_soft_replace_attempt_count") or 0) + 1
                    )
                    rep_map, rep_tr = _p4f._try_atomic_replace_soft_corridor(
                        map_cur,
                        final_mining_map=final_mining_map,
                        pass3_trace=pass3_trace,
                        solver_routing_state=solver_routing_state,
                        old_soft_corridor_cells=old_cells,
                        is_external=is_external,
                        existing_layout_solver_hints=existing_layout_solver_hints,
                    )
                    merged.update(rep_tr)
                    if rep_tr.get("p4_soft_replace_committed"):
                        merged["p4_soft_replace_commit_count"] = (
                            int(merged.get("p4_soft_replace_commit_count") or 0) + 1
                        )
                        extend_recovery_chain(merged, RECOVERY_SEGMENT_SOFT_REPLACE_V2)
                    if rep_map is not None:
                        map_cur = rep_map
                        continue

            merged["p4_reclaim_provisional_last_reject_reason"] = str(rr or "")
            merged["p4_reclaim_provisional_reject_count"] = int(
                merged.get("p4_reclaim_provisional_reject_count") or 0
            ) + 1
            if i + 1 >= max_loop_iterations:
                merged["p4_reclaim_loop_successful_commits"] = commits
                merged["p4_reclaim_loop_internal_transport_cumulative_added"] = spent
                merged["p4_reclaim_loop_terminated_reason"] = (
                    "provisional_commit_failed_max_iterations"
                )
                if commits:
                    merged["p4_reclaim_added_extractor_cells"] = acc_ex
                    merged["p4_reclaim_added_extension_cells"] = acc_ext
                    merged["p4_reclaim_added_stub_cells"] = acc_stub
                elif not merged.get("p4_reclaim_provisional_commit_attempted", False):
                    merged.update(
                        p4_reclaim_provisional_commit_neutral_trace(
                            attempted=True,
                            rollback_reason=str(rr or "provisional_commit_failed"),
                        )
                    )
                return map_cur, merged
            continue

        incr_actual = int(picked.incremental_internal_transport_added)
        if commit_tr.get("p4_reclaim_incremental_route_committed"):
            b2i = commit_tr.get("p4_reclaim_incremental_route_b2_internal_transport_added")
            if b2i is not None:
                incr_actual = int(b2i)

        spent += incr_actual
        commits += 1
        map_cur = map_next
        merged["p4_reclaim_loop_successful_commits"] = commits
        merged["p4_reclaim_loop_internal_transport_cumulative_added"] = spent
        if commit_tr.get("p4_reclaim_incremental_route_committed"):
            acc_route_zone |= _p4_incremental_route_coords_from_commit_trace(commit_tr)
            merged["p4_reclaim_route_zone_excluded_cumulative_count"] = len(acc_route_zone)
            lr = commit_tr.get("p4_reclaim_final_route_cells_added")
            merged["p4_reclaim_last_commit_route_cells"] = list(lr) if isinstance(lr, list) else []
            ls = commit_tr.get("p4_reclaim_soft_protected_candidate_cells_added")
            merged["p4_reclaim_last_soft_protected_candidate_cells"] = (
                list(ls) if isinstance(ls, list) else []
            )

    merged["p4_reclaim_loop_terminated_reason"] = "max_iterations"
    merged["p4_reclaim_added_extractor_cells"] = acc_ex
    merged["p4_reclaim_added_extension_cells"] = acc_ext
    merged["p4_reclaim_added_stub_cells"] = acc_stub
    return map_cur, merged
