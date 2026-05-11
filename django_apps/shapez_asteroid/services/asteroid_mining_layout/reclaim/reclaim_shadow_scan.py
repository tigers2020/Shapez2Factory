"""P4-A: reclaim shadow scan (eval list + trace, no commits)."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    ReclaimShadowScanResult,
    _P4BundleEval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    MAX_RECLAIM_SHADOW_SCAN_LIMIT,
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)

__all__ = (
    "_evaluate_one_shadow_bundle",
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
) -> ReclaimShadowScanResult:
    """P4-A scan: trace dict plus eval list + ``transport_kind`` for P4-B1."""

    if not p4_reclaim_shadow_enabled:
        return reclaim_shadow_scan_result_when_feature_disabled()

    mineable, asteroid = _mineable_and_asteroid_coords(final_mining_map)
    zone_extra = frozenset(p4_committed_route_cells_for_zone or ())
    final_route_cells = _all_transport_cells(map_after_pass3) | zone_extra
    committed = _committed_building_cells(map_after_pass3)
    pcs = protected_corridors_read_for_reclaim(
        pass3_trace=pass3_trace,
        solver_routing_state=solver_routing_state,
        existing_layout_solver_hints=existing_layout_solver_hints,
    )
    hard = pcs.hard
    soft = pcs.soft
    corridor_trace = {
        "p4_reclaim_protected_corridor_source": pcs.source,
        "p4_reclaim_hard_protected_count": len(pcs.hard),
        "p4_reclaim_soft_protected_count": len(pcs.soft),
        "p4_reclaim_existing_layout_hint_cell_count": len(pcs.existing_layout_hints_cells),
    }
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route_cells,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft,
        committed_building_cells=committed,
    )

    reclaimed = _reclaimed_interior_transport_cells(
        map_before_pass3,
        map_after_pass3,
        mineable=mineable,
        asteroid=asteroid,
    )

    raw_cells = cells_dict_from_mining_map(map_after_pass3)
    cells_d = {k: dict(v) for k, v in raw_cells.items()}
    jobs = _collect_routing_jobs(cells_d)
    if not jobs:
        return reclaim_shadow_scan_result_no_routing_jobs(
            zone_route_rebuilt=bool(zone_extra),
            mineable_excluded_by_route_cells=len(mineable & final_route_cells),
            corridor_trace=corridor_trace,
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

    anchor_cells = sorted(mineable_cur & reclaimed, key=lambda p: (p[1], p[0]))
    evals: list[_P4BundleEval] = []
    n_eval = 0
    for anchor in anchor_cells:
        x, y = anchor
        for extension in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if extension not in mineable_cur:
                continue
            for rotation in (0, 1, 2, 3):
                if n_eval >= MAX_RECLAIM_SHADOW_SCAN_LIMIT:
                    break
                n_eval += 1
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
                        soft_protected_corridors=soft,
                        want_role=want_role,
                        is_external=is_external,
                        outlets_order=outlets_order,
                        internal_budget=internal_budget,
                        pass3_raw_saved=pass3_raw_saved,
                        spent_prior=spent_prior,
                        gain_slots=RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS,
                        gain_ratio_threshold=gain_ratio_threshold,
                        shared=shared,
                    )
                )
            if n_eval >= MAX_RECLAIM_SHADOW_SCAN_LIMIT:
                break
        if n_eval >= MAX_RECLAIM_SHADOW_SCAN_LIMIT:
            break

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

    best_for_trace = best_accepted if best_accepted is not None else best_any

    best_dict: dict[str, Any] | None = None
    projected_added = 0
    if best_for_trace is not None:
        incr_it = best_for_trace.incremental_internal_transport_added
        best_dict = {
            "gain": best_for_trace.gain,
            "additional_route_cost": best_for_trace.additional_route_cost,
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
        }
        if best_for_trace.accepted_shadow:
            projected_added = spent_prior + int(best_for_trace.incremental_internal_transport_added)

    trace = {
        **p4_reclaim_shadow_scan_success_trace_prefix(
            zone_route_rebuilt=bool(zone_extra),
            mineable_excluded_by_route_cells=len(mineable & final_route_cells),
        ),
        "p4_reclaim_candidate_count": len(evals),
        "p4_reclaim_accepted_shadow_count": accepted,
        "p4_reclaim_rejected_shadow_count": rejected,
        "p4_reclaim_internal_transport_budget": internal_budget,
        "p4_reclaim_internal_transport_projected_added": projected_added,
        "p4_reclaim_best_candidate": best_dict,
        **corridor_trace,
    }
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
    ).trace
