"""P4-A: reclaim shadow scan (eval list + trace, no commits)."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Set
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    ReclaimShadowScanResult,
    _P4BundleEval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    MAX_RECLAIM_SHADOW_SCAN_LIMIT,
    P4_RECLAIM_ZERO_ALL_TRANSPORT_PROTECTED,
    P4_RECLAIM_ZERO_BUDGET_TOO_LOW,
    P4_RECLAIM_ZERO_GEOMETRY_BLOCKED,
    P4_RECLAIM_ZERO_NO_ANCHOR_NEAR_FREED_CELL,
    P4_RECLAIM_ZERO_NO_MINEABLE_AFTER_EXCLUSIONS,
    P4_RECLAIM_ZERO_NO_RECLAIMED_CELLS,
    RECLAIM_DIVERSITY_MID_RADIUS,
    RECLAIM_DIVERSITY_NEAR_RADIUS,
    RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_read_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _all_transport_cells,
    _allowed_internal_transport_budget,
    _committed_building_cells,
    _mineable_cur_for_reclaim,
    _reclaimed_interior_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_p4_bundle import (
    select_best_accepted_p4_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_scan_eval import (  # noqa: E501
    _build_p4_shadow_scan_shared,
    _evaluate_one_shadow_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_scan_policy import (  # noqa: E501
    p4_reclaim_shadow_scan_success_trace_prefix,
    reclaim_shadow_scan_result_no_routing_jobs,
    reclaim_shadow_scan_result_when_feature_disabled,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    collect_routing_jobs as _collect_routing_jobs,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    mineable_and_asteroid_coords as _mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    mining_map_state_hash,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    _internal_transport_count_for_pass3_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)


def _p4_min_manhattan_to_priors(anchor: Coord, priors: frozenset[Coord]) -> int | None:
    if not priors:
        return None
    return min(abs(anchor[0] - p[0]) + abs(anchor[1] - p[1]) for p in priors)


def _p4_scan_distance_bucket_name(min_d: int | None, *, has_priors: bool) -> str:
    if not has_priors:
        return "all"
    assert min_d is not None
    if min_d <= RECLAIM_DIVERSITY_NEAR_RADIUS:
        return "near"
    if min_d <= RECLAIM_DIVERSITY_MID_RADIUS:
        return "mid"
    return "far"


def _p4_bucketed_anchor_lists_for_scan(
    reclaim_cells: Set[Coord],
    priors: frozenset[Coord],
) -> tuple[dict[str, list[Coord]], tuple[str, ...]]:
    """Partition reclaim anchors into near/mid/far vs priors, or a single ``all`` stream."""
    ordered = sorted(reclaim_cells, key=lambda p: (p[1], p[0]))
    if not priors:
        return {"all": list(ordered)}, ("all",)
    near: list[Coord] = []
    mid: list[Coord] = []
    far: list[Coord] = []
    for a in ordered:
        md = _p4_min_manhattan_to_priors(a, priors)
        assert md is not None
        bn = _p4_scan_distance_bucket_name(md, has_priors=True)
        if bn == "near":
            near.append(a)
        elif bn == "mid":
            mid.append(a)
        else:
            far.append(a)
    return {"near": near, "mid": mid, "far": far}, ("near", "mid", "far")


def _p4_ordered_bundle_specs_for_anchor(
    anchor: Coord,
    mineable_cur: frozenset[Coord],
) -> list[tuple[Coord, int]]:
    x, y = anchor
    out: list[tuple[Coord, int]] = []
    for ext in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if ext not in mineable_cur:
            continue
        for rot in (0, 1, 2, 3):
            out.append((ext, rot))
    return out


def _p4_effective_recent_reclaim_anchors(
    p4_recent_reclaim_anchors: tuple[Coord, ...] | None,
    p4_last_reclaim_anchor: Coord | None,
) -> tuple[Coord, ...] | None:
    if p4_recent_reclaim_anchors is not None:
        return p4_recent_reclaim_anchors if p4_recent_reclaim_anchors else None
    if p4_last_reclaim_anchor is not None:
        return (p4_last_reclaim_anchor,)
    return None


def _p4_nearest_mineable_cur_sample(
    origin: Coord,
    mineable_cur: frozenset[Coord],
) -> dict[str, Any] | None:
    """Nearest mineable_cur cell to a freed interior-transport cell (Manhattan, deterministic)."""

    if not mineable_cur:
        return None
    best_t: Coord | None = None
    best_d: int | None = None
    for t in mineable_cur:
        d = abs(t[0] - origin[0]) + abs(t[1] - origin[1])
        if (
            best_d is None
            or d < best_d
            or (d == best_d and best_t is not None and (t[1], t[0]) < (best_t[1], best_t[0]))
        ):
            best_d = d
            best_t = t
    assert best_t is not None and best_d is not None
    return {
        "freed_cell": [origin[0], origin[1]],
        "nearest_mineable_cur_cell": [best_t[0], best_t[1]],
        "manhattan_distance": int(best_d),
    }


def _p4_mineable_exclusion_sequential_counts(
    mineable_base: frozenset[Coord],
    *,
    final_route_cells: frozenset[Coord],
    hard: frozenset[Coord],
    soft: frozenset[Coord],
    committed: frozenset[Coord],
) -> tuple[int, int, int, int, int]:
    """Exclusive sequential exclusions matching :func:`_mineable_cur_for_reclaim`."""

    m = mineable_base
    ex_route = len(m & final_route_cells)
    after_route = m - final_route_cells
    ex_hard = len(after_route & hard)
    after_hard = after_route - hard
    ex_soft = len(after_hard & soft)
    after_soft = after_hard - soft
    ex_comm = len(after_soft & committed)
    cur = len(after_soft - committed)
    return ex_route, ex_hard, ex_soft, ex_comm, cur


def _p4_reclaim_zero_candidate_diag(
    *,
    mineable_base: frozenset[Coord],
    mineable_cur: frozenset[Coord],
    final_route_cells: frozenset[Coord],
    hard: frozenset[Coord],
    soft: frozenset[Coord],
    committed: frozenset[Coord],
    reclaimed: frozenset[Coord],
    reclaim_anchor_cells: set[Coord],
    transport_cells: frozenset[Coord],
    internal_budget: int,
    spent_prior: int,
    anchor_specs_empty_all: bool,
    has_routing_jobs: bool,
) -> dict[str, Any]:
    """Structured diagnostics when the P4-A scan emits zero bundle evaluations (trace only)."""

    ex_route, ex_hard, ex_soft, ex_comm, cur_check = _p4_mineable_exclusion_sequential_counts(
        mineable_base,
        final_route_cells=final_route_cells,
        hard=hard,
        soft=soft,
        committed=committed,
    )
    assert cur_check == len(mineable_cur)

    transport_total = len(transport_cells)
    unprotected_ct = len(transport_cells - hard - soft)

    reasons: list[str] = []

    def _add(r: str) -> None:
        if r not in reasons:
            reasons.append(r)

    if has_routing_jobs:
        if not reclaimed:
            _add(P4_RECLAIM_ZERO_NO_RECLAIMED_CELLS)
        if not mineable_base:
            _add(P4_RECLAIM_ZERO_NO_MINEABLE_AFTER_EXCLUSIONS)
        elif not mineable_cur:
            _add(P4_RECLAIM_ZERO_NO_MINEABLE_AFTER_EXCLUSIONS)
        if reclaimed and not reclaim_anchor_cells and mineable_cur:
            _add(P4_RECLAIM_ZERO_NO_ANCHOR_NEAR_FREED_CELL)
        if transport_total > 0 and unprotected_ct == 0:
            _add(P4_RECLAIM_ZERO_ALL_TRANSPORT_PROTECTED)
        if reclaim_anchor_cells and anchor_specs_empty_all:
            _add(P4_RECLAIM_ZERO_GEOMETRY_BLOCKED)
        if reclaim_anchor_cells and spent_prior >= internal_budget >= 0:
            _add(P4_RECLAIM_ZERO_BUDGET_TOO_LOW)

    nearest: dict[str, Any] | None = None
    if reclaimed and mineable_cur:
        origin = min(reclaimed, key=lambda c: (c[1], c[0]))
        nearest = _p4_nearest_mineable_cur_sample(origin, mineable_cur)

    failure_samples: list[dict[str, Any]] = []
    if has_routing_jobs and reclaimed and not reclaim_anchor_cells and mineable_cur:
        cell = min(reclaimed, key=lambda c: (c[1], c[0]))
        failure_samples.append(
            {
                "reason_code": P4_RECLAIM_ZERO_NO_ANCHOR_NEAR_FREED_CELL,
                "reclaimed_sample": [cell[0], cell[1]],
            }
        )
    elif has_routing_jobs and reclaim_anchor_cells and anchor_specs_empty_all:
        for a in sorted(reclaim_anchor_cells, key=lambda c: (c[1], c[0]))[:5]:
            failure_samples.append(
                {
                    "reason_code": P4_RECLAIM_ZERO_GEOMETRY_BLOCKED,
                    "anchor": [a[0], a[1]],
                }
            )

    return {
        "p4_reclaim_zero_candidate_reasons": reasons,
        "mineable_base_count": len(mineable_base),
        "excluded_by_final_route_count": ex_route,
        "excluded_by_hard_protected_count": ex_hard,
        "excluded_by_soft_protected_count": ex_soft,
        "excluded_by_committed_placement_count": ex_comm,
        "mineable_cur_count": len(mineable_cur),
        "p4_reclaim_transport_total": transport_total,
        "p4_reclaim_hard_protected_count": len(hard),
        "p4_reclaim_soft_protected_count": len(soft),
        "p4_reclaim_final_route_count": len(final_route_cells),
        "p4_reclaim_unprotected_transport_count": unprotected_ct,
        "reclaim_anchor_candidate_count": len(reclaim_anchor_cells),
        "reclaim_anchor_failure_samples": failure_samples,
        "nearest_freed_cell_to_candidate_sample": nearest,
    }


def _p4_reclaim_scan_preconditions_dict(
    *,
    mineable_cur: frozenset[Coord],
    reclaimed: frozenset[Coord],
    reclaim_cells: Set[Coord],
    routing_jobs_count: int,
) -> dict[str, int]:
    inter = mineable_cur & reclaimed
    return {
        "mineable_cur_count": len(mineable_cur),
        "reclaimed_interior_transport_count": len(reclaimed),
        "reclaim_intersection_count": len(inter),
        "reclaim_anchor_candidate_count": len(reclaim_cells),
        "routing_jobs_count": routing_jobs_count,
    }


def _p4_scan_entry_handoff_trace(
    map_after_pass3: list[dict[str, Any]],
    *,
    is_external: Callable[[Coord], bool],
    scan_preconditions: dict[str, int],
    p4_baseline_internal_transport_at_reclaim_entry: int | None,
    p4_compare_baseline_internal_to_scan_entry: bool,
) -> dict[str, Any]:
    entry_it = _internal_transport_count_for_pass3_kind(
        map_after_pass3,
        is_external=is_external,
    )
    out: dict[str, Any] = {
        "p4_reclaim_scan_preconditions": scan_preconditions,
        "p4_reclaim_internal_transport_at_scan_entry": entry_it,
        "p4_reclaim_entry_transport_cell_count": len(_all_transport_cells(map_after_pass3)),
        "p4_reclaim_entry_mining_map_state_hash": mining_map_state_hash(map_after_pass3),
    }
    if p4_baseline_internal_transport_at_reclaim_entry is not None:
        out["p4_baseline_internal_transport_at_reclaim_entry"] = int(
            p4_baseline_internal_transport_at_reclaim_entry
        )
    if (
        p4_compare_baseline_internal_to_scan_entry
        and p4_baseline_internal_transport_at_reclaim_entry is not None
    ):
        bl = int(p4_baseline_internal_transport_at_reclaim_entry)
        out["p4_reclaim_scan_entry_baseline_mismatch"] = entry_it is None or int(entry_it) != bl
    return out


def _p4_diversity_trace_dict(
    e: _P4BundleEval,
    *,
    frontier_orbit_streak_prior: int = 0,
) -> dict[str, Any]:
    return {
        "min_anchor_distance_to_prior": e.p4_min_anchor_distance_to_prior,
        "local_cluster_density": e.p4_local_cluster_density,
        "route_zone_overlap_cells": e.p4_route_zone_overlap_cells,
        "cluster_penalty": e.p4_cluster_penalty,
        "route_zone_penalty": e.p4_route_zone_penalty,
        "total_diversity_penalty": e.p4_total_diversity_penalty,
        "gain_ratio_adjusted": e.gain_ratio_adjusted,
        "distance_bucket": e.p4_distance_bucket,
        "continuity_bonus": e.p4_continuity_bonus,
        "min_recent_anchor_distance": e.p4_min_recent_anchor_distance,
        "continuity_distance": e.p4_min_recent_anchor_distance,
        "final_diversity_score": e.p4_final_diversity_score,
        "continuity_band_state": e.p4_continuity_band_state,
        "continuity_winning_index": e.p4_continuity_winning_index,
        "continuity_window_size": e.p4_continuity_window_size,
        "continuity_max_weighted_t": e.p4_continuity_max_weighted_t,
        "continuity_mean_t": e.p4_continuity_mean_t,
        "frontier_orbit_score": frontier_orbit_streak_prior,
    }


__all__ = (
    "_evaluate_one_shadow_bundle",
    "_p4_bucketed_anchor_lists_for_scan",
    "_p4_min_manhattan_to_priors",
    "_p4_ordered_bundle_specs_for_anchor",
    "_p4_scan_distance_bucket_name",
    "reclaim_shadow_scan_core_after_pass3",
    "run_reclaim_shadow_scan_after_pass3",
)


def reclaim_shadow_scan_core_after_pass3(
    map_before_pass3: list[dict[str, Any]],
    map_after_pass3: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    pass3_trace: dict[str, Any],
    solver_routing_state: Mapping[str, object] | None = None,
    existing_layout_solver_hints: Mapping[str, object] | None = None,
    p4_reclaim_shadow_enabled: bool = True,
    gain_ratio_threshold: float = DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    reclaim_internal_transport_spent_prior: int = 0,
    p4_committed_route_cells_for_zone: frozenset[Coord] | None = None,
    p4_prior_reclaim_anchors: frozenset[Coord] | None = None,
    p4_last_reclaim_anchor: Coord | None = None,
    p4_recent_reclaim_anchors: tuple[Coord, ...] | None = None,
    p4_frontier_orbit_streak_prior: int = 0,
    p4_baseline_internal_transport_at_reclaim_entry: int | None = None,
    p4_compare_baseline_internal_to_scan_entry: bool = False,
) -> ReclaimShadowScanResult:
    """P4-A scan: trace dict plus eval list + ``transport_kind`` for P4-B1."""

    if not p4_reclaim_shadow_enabled:
        return reclaim_shadow_scan_result_when_feature_disabled()

    mineable, asteroid = _mineable_and_asteroid_coords(final_mining_map)
    zone_extra = frozenset(p4_committed_route_cells_for_zone or ())
    priors = frozenset(p4_prior_reclaim_anchors or ())
    final_route_cells = _all_transport_cells(map_after_pass3) | zone_extra
    committed = _committed_building_cells(map_after_pass3)
    pcs = protected_corridors_read_for_reclaim(
        pass3_trace=pass3_trace,
        solver_routing_state=solver_routing_state,
        existing_layout_solver_hints=existing_layout_solver_hints,
    )
    hard = pcs.hard
    soft = pcs.soft
    transport_on_map = _all_transport_cells(map_after_pass3)
    soft_active = frozenset(c for c in soft if c in transport_on_map)
    corridor_trace = {
        "p4_reclaim_protected_corridor_source": pcs.source,
        "p4_reclaim_hard_protected_count": len(pcs.hard),
        "p4_reclaim_soft_protected_count": len(pcs.soft),
        "p4_reclaim_soft_active_on_map_count": len(soft_active),
        "p4_reclaim_existing_layout_hint_cell_count": len(pcs.existing_layout_hints_cells),
        "p4_reclaim_probe_discarded_cell_count": len(pcs.probe_discarded_cells),
    }
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route_cells,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft_active,
        committed_building_cells=committed,
    )

    reclaimed = _reclaimed_interior_transport_cells(
        map_before_pass3,
        map_after_pass3,
        is_external=is_external,
    )

    raw_cells = cells_dict_from_mining_map(map_after_pass3)
    cells_d = {k: dict(v) for k, v in raw_cells.items()}
    jobs = _collect_routing_jobs(cells_d)
    if not jobs:
        reclaim_cells_nr = mineable_cur & reclaimed
        pre_nr = _p4_reclaim_scan_preconditions_dict(
            mineable_cur=mineable_cur,
            reclaimed=reclaimed,
            reclaim_cells=reclaim_cells_nr,
            routing_jobs_count=0,
        )
        extra_nr = _p4_scan_entry_handoff_trace(
            map_after_pass3,
            is_external=is_external,
            scan_preconditions=pre_nr,
            p4_baseline_internal_transport_at_reclaim_entry=p4_baseline_internal_transport_at_reclaim_entry,
            p4_compare_baseline_internal_to_scan_entry=p4_compare_baseline_internal_to_scan_entry,
        )
        pass3_saved_nr = int(pass3_trace.get("pass3_internal_transport_saved") or 0)
        budget_nr = _allowed_internal_transport_budget(pass3_saved_nr)
        spent_nr = max(0, int(reclaim_internal_transport_spent_prior))
        zero_nr = _p4_reclaim_zero_candidate_diag(
            mineable_base=frozenset(mineable),
            mineable_cur=mineable_cur,
            final_route_cells=final_route_cells,
            hard=hard,
            soft=soft_active,
            committed=committed,
            reclaimed=reclaimed,
            reclaim_anchor_cells=set(reclaim_cells_nr),
            transport_cells=_all_transport_cells(map_after_pass3),
            internal_budget=budget_nr,
            spent_prior=spent_nr,
            anchor_specs_empty_all=False,
            has_routing_jobs=False,
        )
        return reclaim_shadow_scan_result_no_routing_jobs(
            zone_route_rebuilt=bool(zone_extra),
            mineable_excluded_by_route_cells=len(mineable & final_route_cells),
            corridor_trace=corridor_trace,
            extra_trace={**extra_nr, **zero_nr},
        )

    reclaim_cells = mineable_cur & reclaimed
    scan_pre = _p4_reclaim_scan_preconditions_dict(
        mineable_cur=mineable_cur,
        reclaimed=reclaimed,
        reclaim_cells=reclaim_cells,
        routing_jobs_count=len(jobs),
    )

    tk = jobs[0][2]
    want_role = _want_role(tk)
    outlets_order = [j[1] for j in jobs]

    pass3_saved = int(pass3_trace.get("pass3_internal_transport_saved") or 0)
    pass3_raw_saved = pass3_saved
    internal_budget = _allowed_internal_transport_budget(pass3_saved)
    spent_prior = max(0, int(reclaim_internal_transport_spent_prior))

    shared = _build_p4_shadow_scan_shared(
        map_after_pass3,
        want_role=want_role,
        is_external=is_external,
        outlets_order=outlets_order,
        mineable=mineable,
        asteroid=asteroid,
    )

    buckets_map, bucket_order = _p4_bucketed_anchor_lists_for_scan(reclaim_cells, priors)
    anchors_union: set[Coord] = set()
    for b in bucket_order:
        anchors_union.update(buckets_map[b])
    specs: dict[Coord, list[tuple[Coord, int]]] = {
        a: _p4_ordered_bundle_specs_for_anchor(a, mineable_cur) for a in anchors_union
    }
    spec_idx: dict[Coord, int] = {a: 0 for a in anchors_union}
    ptr: dict[str, int] = {b: 0 for b in bucket_order}

    recent_eff = _p4_effective_recent_reclaim_anchors(
        p4_recent_reclaim_anchors,
        p4_last_reclaim_anchor,
    )

    def _try_emit_one(bucket: str) -> tuple[Coord, Coord, int] | None:
        lst = buckets_map[bucket]
        while ptr[bucket] < len(lst):
            a = lst[ptr[bucket]]
            si = spec_idx[a]
            sp = specs[a]
            if si < len(sp):
                ext, rot = sp[si]
                spec_idx[a] = si + 1
                return (a, ext, rot)
            ptr[bucket] += 1
        return None

    evals: list[_P4BundleEval] = []
    scan_slot_order: list[dict[str, Any]] = []
    n_eval = 0
    rr_cycle = 0
    has_priors = bool(priors)
    while n_eval < MAX_RECLAIM_SHADOW_SCAN_LIMIT:
        progressed = False
        for bucket in bucket_order:
            if n_eval >= MAX_RECLAIM_SHADOW_SCAN_LIMIT:
                break
            got = _try_emit_one(bucket)
            if got is None:
                continue
            anchor, extension, rotation = got
            progressed = True
            min_d = _p4_min_manhattan_to_priors(anchor, priors) if has_priors else None
            scan_bucket = _p4_scan_distance_bucket_name(min_d, has_priors=has_priors)
            evals.append(
                _evaluate_one_shadow_bundle(
                    anchor=anchor,
                    extension=extension,
                    rotation=rotation,
                    map_after_pass3=map_after_pass3,
                    mineable=mineable,
                    asteroid=asteroid,
                    mineable_cur=mineable_cur,
                    final_route_cells=final_route_cells,
                    hard_protected_corridors=hard,
                    soft_protected_corridors=soft_active,
                    want_role=want_role,
                    is_external=is_external,
                    outlets_order=outlets_order,
                    internal_budget=internal_budget,
                    pass3_raw_saved=pass3_raw_saved,
                    spent_prior=spent_prior,
                    gain_slots=RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS,
                    gain_ratio_threshold=gain_ratio_threshold,
                    shared=shared,
                    prior_reclaim_anchors=priors if priors else None,
                    route_zone_cells_for_overlap=zone_extra if zone_extra else None,
                    recent_reclaim_anchors=recent_eff,
                    scan_distance_bucket=scan_bucket,
                )
            )
            scan_slot_order.append(
                {
                    "slot_index": n_eval,
                    "rr_bucket_cycle": rr_cycle,
                    "distance_bucket": scan_bucket,
                    "anchor": [anchor[0], anchor[1]],
                    "extension": [extension[0], extension[1]],
                    "rotation": rotation,
                }
            )
            n_eval += 1
        if not progressed:
            break
        rr_cycle += 1

    accepted = sum(1 for e in evals if e.accepted_shadow)
    rejected = len(evals) - accepted

    best_accepted = select_best_accepted_p4_bundle(evals)
    best_any: _P4BundleEval | None = None
    for e in evals:
        if best_any is None or e.gain_ratio > best_any.gain_ratio:
            best_any = e
        elif best_any is not None and math.isclose(e.gain_ratio, best_any.gain_ratio):
            if e.additional_route_cost < best_any.additional_route_cost:
                best_any = e
            elif math.isclose(e.additional_route_cost, best_any.additional_route_cost):
                if e.p4_final_diversity_score < best_any.p4_final_diversity_score:
                    best_any = e

    best_for_trace = best_accepted if best_accepted is not None else best_any

    best_dict: dict[str, Any] | None = None
    projected_added = 0
    if best_for_trace is not None:
        incr_it = best_for_trace.incremental_internal_transport_added
        best_dict = {
            "gain": best_for_trace.gain,
            "additional_route_cost": best_for_trace.additional_route_cost,
            "route_cost_including_stub": best_for_trace.additional_route_cost,
            "route_cost_first_hop_from_stub": best_for_trace.p4_route_cost_first_hop_from_stub,
            "route_cost_after_stub": best_for_trace.p4_route_cost_after_stub,
            "gain_ratio": (
                best_for_trace.gain_ratio if not math.isinf(best_for_trace.gain_ratio) else None
            ),
            "incremental_internal_transport_added": incr_it,
            "rejected_reason": best_for_trace.rejected_reason,
            "anchor": [best_for_trace.anchor[0], best_for_trace.anchor[1]],
            "extension": [best_for_trace.extension[0], best_for_trace.extension[1]],
            "rotation": best_for_trace.rotation,
            "shadow_route_path": (
                [[int(c[0]), int(c[1])] for c in best_for_trace.shadow_route_path]
                if best_for_trace.shadow_route_path
                else None
            ),
            "p4_diversity": _p4_diversity_trace_dict(
                best_for_trace,
                frontier_orbit_streak_prior=p4_frontier_orbit_streak_prior,
            ),
        }
        if best_for_trace.accepted_shadow:
            projected_added = spent_prior + int(best_for_trace.incremental_internal_transport_added)

    trace = {
        **p4_reclaim_shadow_scan_success_trace_prefix(
            zone_route_rebuilt=bool(zone_extra),
            mineable_excluded_by_route_cells=len(mineable & final_route_cells),
        ),
        **_p4_scan_entry_handoff_trace(
            map_after_pass3,
            is_external=is_external,
            scan_preconditions=scan_pre,
            p4_baseline_internal_transport_at_reclaim_entry=p4_baseline_internal_transport_at_reclaim_entry,
            p4_compare_baseline_internal_to_scan_entry=p4_compare_baseline_internal_to_scan_entry,
        ),
        "p4_reclaim_candidate_count": len(evals),
        "p4_reclaim_accepted_shadow_count": accepted,
        "p4_reclaim_rejected_shadow_count": rejected,
        "p4_reclaim_internal_transport_budget": internal_budget,
        "p4_reclaim_internal_transport_projected_added": projected_added,
        "p4_reclaim_best_candidate": best_dict,
        "p4_reclaim_scan_slot_order": scan_slot_order,
        "p4_reclaim_frontier_orbit_streak_prior": p4_frontier_orbit_streak_prior,
        **corridor_trace,
    }
    if not evals:
        anchor_specs_empty_all = bool(reclaim_cells) and all(
            len(specs.get(a, ())) == 0 for a in reclaim_cells
        )
        trace.update(
            _p4_reclaim_zero_candidate_diag(
                mineable_base=frozenset(mineable),
                mineable_cur=mineable_cur,
                final_route_cells=final_route_cells,
                hard=hard,
                soft=soft_active,
                committed=committed,
                reclaimed=reclaimed,
                reclaim_anchor_cells=set(reclaim_cells),
                transport_cells=_all_transport_cells(map_after_pass3),
                internal_budget=internal_budget,
                spent_prior=spent_prior,
                anchor_specs_empty_all=anchor_specs_empty_all,
                has_routing_jobs=True,
            )
        )
    return ReclaimShadowScanResult(trace=trace, evals=evals, transport_kind=tk)


def run_reclaim_shadow_scan_after_pass3(
    map_before_pass3: list[dict[str, Any]],
    map_after_pass3: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    pass3_trace: dict[str, Any],
    solver_routing_state: Mapping[str, object] | None = None,
    existing_layout_solver_hints: Mapping[str, object] | None = None,
    p4_reclaim_shadow_enabled: bool = True,
    gain_ratio_threshold: float = DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    reclaim_internal_transport_spent_prior: int = 0,
    p4_committed_route_cells_for_zone: frozenset[Coord] | None = None,
    p4_prior_reclaim_anchors: frozenset[Coord] | None = None,
    p4_last_reclaim_anchor: Coord | None = None,
    p4_recent_reclaim_anchors: tuple[Coord, ...] | None = None,
    p4_frontier_orbit_streak_prior: int = 0,
    p4_baseline_internal_transport_at_reclaim_entry: int | None = None,
    p4_compare_baseline_internal_to_scan_entry: bool = False,
) -> dict[str, Any]:
    """Scan shadow reclaim bundles after Pass3; emit trace only (no commits)."""

    return reclaim_shadow_scan_core_after_pass3(
        map_before_pass3,
        map_after_pass3,
        final_mining_map=final_mining_map,
        is_external=is_external,
        pass3_trace=pass3_trace,
        solver_routing_state=solver_routing_state,
        existing_layout_solver_hints=existing_layout_solver_hints,
        p4_reclaim_shadow_enabled=p4_reclaim_shadow_enabled,
        gain_ratio_threshold=gain_ratio_threshold,
        reclaim_internal_transport_spent_prior=reclaim_internal_transport_spent_prior,
        p4_committed_route_cells_for_zone=p4_committed_route_cells_for_zone,
        p4_prior_reclaim_anchors=p4_prior_reclaim_anchors,
        p4_last_reclaim_anchor=p4_last_reclaim_anchor,
        p4_recent_reclaim_anchors=p4_recent_reclaim_anchors,
        p4_frontier_orbit_streak_prior=p4_frontier_orbit_streak_prior,
        p4_baseline_internal_transport_at_reclaim_entry=p4_baseline_internal_transport_at_reclaim_entry,
        p4_compare_baseline_internal_to_scan_entry=p4_compare_baseline_internal_to_scan_entry,
    ).trace
