"""P4-B1 provisional placement + optional P4-B2 incremental route commit."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    ReclaimShadowScanResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P4_REJECT_FINAL_ROUTE_OVERLAP,
    P4_REJECT_NO_OUTPUT_STUB,
    P4_REJECT_NO_SHADOW_CANDIDATE,
    P4_REJECT_SOFT_PROTECTED_CORRIDOR,
    P4_REJECT_VALIDATION,
    P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED,
    P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_read_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _all_transport_cells,
    _committed_building_cells,
    _mining_map_snapshot,
    _p4_overlap_reject_reason,
    _provisional_reclaim_layout_rows,
    _rebuild_mining_map_from_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_p4_bundle import (
    _p4_selected_candidate_rank,
    select_best_accepted_p4_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    layout_kind as _layout_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    mineable_and_asteroid_coords as _mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)

from .reclaim_shadow_commit_b2_incremental import _p4_b2_try_commit_incremental_route
from .reclaim_shadow_commit_policy import (
    p4_incremental_route_commit_will_run,
    p4_incremental_route_skip_reason_for_trace,
    p4_provisional_commit_entry_skip_reason,
)
from .reclaim_shadow_commit_trace import (
    p4_b2_incremental_route_neutral_trace,
    p4_reclaim_provisional_commit_neutral_trace,
)


def run_p4_reclaim_provisional_commit_after_pass3(
    mining_map: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    pass3_trace: dict[str, Any],
    solver_routing_state: Mapping[str, object] | None,
    scan_result: ReclaimShadowScanResult,
    p4_reclaim_provisional_commit_enabled: bool = True,
    is_external: Callable[[Coord], bool] | None = None,
    p4_reclaim_incremental_route_commit_enabled: bool = True,
    existing_layout_solver_hints: Mapping[str, object] | None = None,
    reclaim_internal_transport_spent_prior: int = 0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """P4-B1 provisional placement + optional P4-B2 incremental route commit."""

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow as _p4f  # noqa: E501

    neutral = p4_reclaim_provisional_commit_neutral_trace(attempted=False)
    tr = scan_result.trace
    entry_skip = p4_provisional_commit_entry_skip_reason(
        provisional_enabled=p4_reclaim_provisional_commit_enabled,
        scan_trace=tr,
    )
    if entry_skip is not None:
        out = dict(neutral)
        out["p4_reclaim_provisional_commit_skip_reason"] = entry_skip
        return mining_map, out

    tk = scan_result.transport_kind
    if tk is None:
        out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
        out["p4_reclaim_provisional_commit_rollback_reason"] = P4_REJECT_NO_SHADOW_CANDIDATE
        return mining_map, out

    picked = select_best_accepted_p4_bundle(scan_result.evals)
    if picked is None:
        out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
        out["p4_reclaim_provisional_commit_rollback_reason"] = P4_REJECT_NO_SHADOW_CANDIDATE
        return mining_map, out

    mineable, _ = _mineable_and_asteroid_coords(final_mining_map)
    final_route_cells = _all_transport_cells(mining_map)
    committed = _committed_building_cells(mining_map)
    pcs = protected_corridors_read_for_reclaim(
        pass3_trace=pass3_trace,
        solver_routing_state=solver_routing_state,
        existing_layout_solver_hints=existing_layout_solver_hints,
    )
    hard, soft = pcs.hard, pcs.soft
    transport_cells_f = _all_transport_cells(mining_map)
    soft_active = frozenset(c for c in soft if c in transport_cells_f)

    snapshot = _mining_map_snapshot(mining_map)
    cells = {k: dict(v) for k, v in cells_dict_from_mining_map(snapshot).items()}

    try:
        miner_row, ext_row, stub_row, stub = _provisional_reclaim_layout_rows(
            anchor=picked.anchor,
            extension=picked.extension,
            rotation=picked.rotation,
            transport_kind=tk,
        )
    except ValueError:
        out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
        out["p4_reclaim_provisional_commit_rollback_reason"] = P4_REJECT_NO_OUTPUT_STUB
        return mining_map, out

    placed = frozenset({picked.anchor, picked.extension, stub})
    reason = _p4_overlap_reject_reason(
        placed,
        final_route_cells=final_route_cells,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft_active,
        committed_building_cells=committed,
    )
    if reason is not None:
        out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
        out["p4_reclaim_provisional_commit_rollback_reason"] = reason
        out["p4_reclaim_selected_candidate"] = {
            "anchor": [picked.anchor[0], picked.anchor[1]],
            "extension": [picked.extension[0], picked.extension[1]],
            "rotation": picked.rotation,
            "gain": picked.gain,
            "additional_route_cost": picked.additional_route_cost,
            "gain_ratio": picked.gain_ratio if not math.isinf(picked.gain_ratio) else None,
            "incremental_internal_transport_added": picked.incremental_internal_transport_added,
        }
        out["p4_reclaim_selected_candidate_rank"] = _p4_selected_candidate_rank(
            scan_result.evals, picked
        )
        if reason == P4_REJECT_SOFT_PROTECTED_CORRIDOR:
            hit_soft = frozenset(placed) & soft
            transport_hits: list[list[int]] = []
            for c in sorted(hit_soft, key=lambda p: (p[1], p[0])):
                prev_row = cells.get(c)
                if prev_row is not None and prev_row.get("role") in ("belt", "pipe"):
                    transport_hits.append([int(c[0]), int(c[1])])
            out["p4_reclaim_soft_corridor_transport_collision_cells"] = transport_hits
        else:
            out["p4_reclaim_soft_corridor_transport_collision_cells"] = []
        return mining_map, out

    for coord, row in (
        (picked.anchor, miner_row),
        (picked.extension, ext_row),
        (stub, stub_row),
    ):
        prev = cells.get(coord)
        if prev is not None:
            role = prev.get("role")
            lk = _layout_kind(prev)
            if role == "occupied" and lk not in (None, "asteroid_field"):
                out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
                out["p4_reclaim_provisional_commit_rollback_reason"] = P4_REJECT_VALIDATION
                return mining_map, out
            if role in ("belt", "pipe"):
                out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
                out["p4_reclaim_provisional_commit_rollback_reason"] = P4_REJECT_FINAL_ROUTE_OVERLAP
                return mining_map, out

        if coord not in mineable:
            out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
            out["p4_reclaim_provisional_commit_rollback_reason"] = P4_REJECT_VALIDATION
            return mining_map, out

        cells[coord] = row

    trial_map = _rebuild_mining_map_from_cells(cells)
    post_final_route = _all_transport_cells(trial_map)
    if frozenset({picked.anchor, picked.extension}) & post_final_route:
        out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
        out["p4_reclaim_provisional_commit_rollback_performed"] = True
        out["p4_reclaim_provisional_commit_rollback_reason"] = P4_REJECT_FINAL_ROUTE_OVERLAP
        out["p4_reclaim_selected_candidate"] = {
            "anchor": [picked.anchor[0], picked.anchor[1]],
            "extension": [picked.extension[0], picked.extension[1]],
            "rotation": picked.rotation,
            "gain": picked.gain,
            "additional_route_cost": picked.additional_route_cost,
            "gain_ratio": picked.gain_ratio if not math.isinf(picked.gain_ratio) else None,
            "incremental_internal_transport_added": picked.incremental_internal_transport_added,
        }
        out["p4_reclaim_selected_candidate_rank"] = _p4_selected_candidate_rank(
            scan_result.evals, picked
        )
        return mining_map, out

    # P4-B2.1: geometry/overlap/stub row gate before B2; full connectivity on trial_map is
    # not required when incremental route commit will run (route is applied before final check).
    report_trial = _p4f.validate_final_mining_layout(trial_map)
    if not report_trial.geometry_valid:
        out = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
        out["p4_reclaim_provisional_commit_rollback_performed"] = True
        out["p4_reclaim_provisional_commit_rollback_reason"] = (
            P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE
        )
        out["p4_reclaim_selected_candidate"] = {
            "anchor": [picked.anchor[0], picked.anchor[1]],
            "extension": [picked.extension[0], picked.extension[1]],
            "rotation": picked.rotation,
            "gain": picked.gain,
            "additional_route_cost": picked.additional_route_cost,
            "gain_ratio": picked.gain_ratio if not math.isinf(picked.gain_ratio) else None,
            "incremental_internal_transport_added": picked.incremental_internal_transport_added,
        }
        out["p4_reclaim_selected_candidate_rank"] = _p4_selected_candidate_rank(
            scan_result.evals, picked
        )
        return mining_map, out

    rank = _p4_selected_candidate_rank(scan_result.evals, picked)
    spath = picked.shadow_route_path
    sel = {
        "anchor": [picked.anchor[0], picked.anchor[1]],
        "extension": [picked.extension[0], picked.extension[1]],
        "rotation": picked.rotation,
        "gain": picked.gain,
        "additional_route_cost": picked.additional_route_cost,
        "gain_ratio": picked.gain_ratio if not math.isinf(picked.gain_ratio) else None,
        "incremental_internal_transport_added": picked.incremental_internal_transport_added,
        "shadow_route_path": [[c[0], c[1]] for c in spath] if spath else None,
    }

    b1_trace = {
        "p4_reclaim_provisional_commit_attempted": True,
        "p4_reclaim_provisional_commit_committed": True,
        "p4_reclaim_provisional_commit_rollback_performed": False,
        "p4_reclaim_provisional_commit_rollback_reason": None,
        "p4_reclaim_selected_candidate": sel,
        "p4_reclaim_selected_candidate_rank": rank,
        "p4_reclaim_added_extractor_cells": [[picked.anchor[0], picked.anchor[1]]],
        "p4_reclaim_added_extension_cells": [[picked.extension[0], picked.extension[1]]],
        "p4_reclaim_added_stub_cells": [[stub[0], stub[1]]],
        "p4_reclaim_provisional_commit_skip_reason": None,
    }

    b2_will_run = p4_incremental_route_commit_will_run(
        p4_reclaim_incremental_route_commit_enabled, is_external
    )

    if b2_will_run:
        assert is_external is not None
        ps_b = scan_result.trace.get("pass3_internal_transport_saved_for_reclaim_budget")
        pass_budget = int(ps_b) if isinstance(ps_b, int) and not isinstance(ps_b, bool) else None
        route_map, b2_trace = _p4_b2_try_commit_incremental_route(
            trial_map,
            picked=picked,
            transport_kind=tk,
            pass3_trace=pass3_trace,
            final_mining_map=final_mining_map,
            is_external=is_external,
            reclaim_internal_transport_spent_prior=reclaim_internal_transport_spent_prior,
            pass3_internal_transport_saved_for_budget=pass_budget,
        )
        if route_map is None:
            ft = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
            ft["p4_reclaim_provisional_commit_rollback_performed"] = True
            ft["p4_reclaim_provisional_commit_rollback_reason"] = (
                b2_trace.get("p4_reclaim_incremental_route_rollback_reason")
                or P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED
            )
            ft["p4_reclaim_selected_candidate"] = sel
            ft["p4_reclaim_selected_candidate_rank"] = rank
            ft.update(b2_trace)
            return mining_map, ft

        return route_map, {**b1_trace, **b2_trace}

    if not report_trial.connectivity_valid:
        ft = p4_reclaim_provisional_commit_neutral_trace(attempted=True)
        ft["p4_reclaim_provisional_commit_rollback_performed"] = True
        ft["p4_reclaim_provisional_commit_rollback_reason"] = (
            P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE
        )
        ft["p4_reclaim_selected_candidate"] = sel
        ft["p4_reclaim_selected_candidate_rank"] = rank
        b2_skip = p4_incremental_route_skip_reason_for_trace(
            p4_reclaim_incremental_route_commit_enabled
        )
        ft.update(p4_b2_incremental_route_neutral_trace(skip_reason=b2_skip))
        return mining_map, ft

    b2_skip = p4_incremental_route_skip_reason_for_trace(
        p4_reclaim_incremental_route_commit_enabled
    )
    return trial_map, {
        **b1_trace,
        **p4_b2_incremental_route_neutral_trace(skip_reason=b2_skip),
    }
