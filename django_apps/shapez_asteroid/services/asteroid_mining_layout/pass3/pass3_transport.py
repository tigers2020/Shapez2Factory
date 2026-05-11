"""Pass-3 mining-priority transport reconstruction (façade re-exports + main entry)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    COMMIT_REASON_GUARDED_ATOMIC,
    MAX_ROUTE_LENGTH_RATIO,
    P3E2_SHADOW_ENABLED_DEFAULT,
    P3E3_ATOMIC_SKIPPED_SHADOW_LEX_INCOMPLETE,
    P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_ROUTE_LENGTH_RATIO,
    P3E3_REJECT_VALIDATION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e2_shadow import (
    _p3e2_shadow_trace,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded import (
    P3E3GuardedCommitCandidate,
    _p3e3_atomic_phase_deferred_by_shadow_alignment,
    _p3e3_atomic_trace_from_dto,
    _p3e3_build_atomic_candidate_map,
    _p3e3_rollback_guarded_transport_cells,
    _p3e3_route_length_ratio_allowed,
    _p3e3_run_atomic_candidate_phase,
    _p3e3_should_commit_guarded_candidate,
    _p3e3_transport_dict_from_candidate_cells,
    p3e2_pass3_summary_placeholder,
    p3e3_emit_guarded_trace,
    p3e3_pass3_summary_placeholder,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_transport_trial import (  # noqa: E501
    _p3e3_validate_guarded_swap_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    Pass3TransportResult,
    mining_map_after_transport_reconstruction,
    mining_priority_route_cell_cost,
    pick_pass3_anchor_transport_cell,
    placement_stub_route_probe_path,
    placement_stub_route_to_trunk_feasible,
    reconstruct_mining_priority_transport,
    transport_connects_outlets_to_anchor,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_trace_summary import (
    pass3_skip_summary,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    collect_routing_jobs,
    mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as transport_kind_to_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_permission import (
    p3e3_guarded_commit_effective_enabled,
)


def run_pass3_transport_minimization_from_maps(
    mining_map: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    p3e3_guarded_commit_enabled: bool | None = None,
    pass3_recovery_context: bool = False,
) -> tuple[list[dict[str, Any]], Pass3TransportResult | None, dict[str, Any]]:
    """Run greedy Pass3 compression on an existing layout (typically post-STEP4).

    ``p3e3_guarded_commit_enabled`` overrides ``P3E3_GUARDED_COMMIT_ENABLED_DEFAULT`` for
    P3-E3 guarded lex commit. When enabled, emits precheck trace and atomic candidate validation;
    if the candidate passes pre-commit checks, applies a live swap and runs post-commit
    ``validate_final_mining_layout`` (rollback to greedy snapshot on failure).

    ``pass3_recovery_context``: when True, ``reconstruct_mining_priority_transport`` may use
    ``allow_degraded_connected_commit`` (gain 0 but connectivity preserved). Default False so
    ``commit_reason=degraded_connected_recovery`` never appears on the main solver path.
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        cells_dict_from_mining_map,
    )

    guarded_on = p3e3_guarded_commit_effective_enabled(p3e3_guarded_commit_enabled)

    raw = cells_dict_from_mining_map(mining_map)
    cells = {k: dict(v) for k, v in raw.items()}
    jobs = collect_routing_jobs(cells)
    if not jobs:
        return (
            mining_map,
            None,
            pass3_skip_summary(
                skip_reason="no_routing_jobs",
                rejected_reason="pass3_skipped_no_routing_jobs",
            ),
        )

    transport_kinds = {j[2] for j in jobs}
    if len(transport_kinds) != 1:
        return (
            mining_map,
            None,
            pass3_skip_summary(
                skip_reason="mixed_transport_kind_mvp",
                rejected_reason="pass3_skipped_mixed_transport_kind_mvp",
            ),
        )

    tk = jobs[0][2]
    wr = transport_kind_to_role(tk)
    outlets_order = [j[1] for j in jobs]
    anchor = pick_pass3_anchor_transport_cell(cells, want_role=wr, is_external=is_external)
    if anchor is None:
        return (
            mining_map,
            None,
            pass3_skip_summary(
                skip_reason="no_anchor",
                rejected_reason="pass3_skipped_no_anchor",
            ),
        )

    tc: dict[Coord, str] = {}
    for c, row in cells.items():
        if row.get("role") == wr:
            tc[c] = wr

    if not tc:
        return (
            mining_map,
            None,
            pass3_skip_summary(
                skip_reason="no_transport_cells",
                rejected_reason="pass3_skipped_no_transport_cells",
            ),
        )

    before_transport_count = len(tc)
    mineable, asteroid = mineable_and_asteroid_coords(final_mining_map)
    asteroid_set = set(asteroid)
    before_internal_transport_count = len(set(tc) & asteroid_set)
    mineable_f = frozenset(mineable)
    asteroid_f = frozenset(asteroid)
    shadow_trace = _p3e2_shadow_trace(
        mining_map=mining_map,
        cells=cells,
        transport_cells=tc,
        outlets_order=outlets_order,
        anchor=anchor,
        transport_kind=tk,
        asteroid_cells=asteroid_set,
        mineable_f=mineable_f,
        asteroid_f=asteroid_f,
        is_external=is_external,
        shadow_enabled=P3E2_SHADOW_ENABLED_DEFAULT,
    )
    p3e3_trace = p3e3_emit_guarded_trace(
        guarded_enabled=guarded_on,
        shadow_trace=shadow_trace,
        outlet_stub_cells=tuple(outlets_order),
    )
    atomic_dto: P3E3GuardedCommitCandidate | None = None
    candidate_validation_passed: bool | None = None
    would_accept_flag: bool | None = None
    if guarded_on:
        if _p3e3_atomic_phase_deferred_by_shadow_alignment(shadow_trace):
            p3e3_trace["p3e3_guarded_atomic_skipped_reason"] = (
                P3E3_ATOMIC_SKIPPED_SHADOW_LEX_INCOMPLETE
            )
        else:
            atomic_dto, atomic_trace = _p3e3_run_atomic_candidate_phase(
                mining_map=mining_map,
                cells=cells,
                transport_cells=tc,
                outlets_order=outlets_order,
                anchor=anchor,
                want_role=wr,
                transport_kind=tk,
                asteroid_cells=asteroid_set,
                mineable_f=mineable_f,
                asteroid_f=asteroid_f,
                is_external=is_external,
            )
            p3e3_trace.update(atomic_trace)
            candidate_validation_passed = atomic_trace.get("p3e3_candidate_validation_passed")
            would_accept_flag = atomic_trace.get("p3e3_guarded_commit_would_accept")

    greedy_result = reconstruct_mining_priority_transport(
        anchor=anchor,
        asteroid_cells=asteroid_set,
        mineable_cells=set(mineable),
        buildings={},
        transport_cells=tc,
        outlets_order=outlets_order,
        transport_role=tk,
        allow_degraded_connected_commit=bool(pass3_recovery_context),
    )
    # Greedy Pass3 output before optional guarded swap (P3-E3b-2b rollback restores this snapshot).
    known_good_transport_snapshot = dict(greedy_result.transport_cells)

    should_commit = _p3e3_should_commit_guarded_candidate(
        guarded_enabled=guarded_on,
        candidate=atomic_dto,
        candidate_validation_passed=candidate_validation_passed,
        would_accept=would_accept_flag,
    )
    post_commit_passed: bool | None = None
    rollback_performed = False
    rollback_reason: str | None = None
    guarded_committed_outcome = False

    if should_commit and atomic_dto is not None:
        candidate_tc = _p3e3_transport_dict_from_candidate_cells(
            atomic_dto.candidate_transport_cells,
            want_role=wr,
        )
        post_ok, post_fail_reason = _p3e3_validate_guarded_swap_mining_map(
            mining_map=mining_map,
            transport_cells=candidate_tc,
            want_role=wr,
            candidate_transport_cells=atomic_dto.candidate_transport_cells,
            fixed_output_stubs=frozenset(outlets_order),
            hard_protected_corridors=atomic_dto.hard_protected_corridors,
        )
        post_commit_passed = post_ok
        if post_ok:
            final_tc = candidate_tc
            gain_atomic = max(0, before_transport_count - len(final_tc))
            result = Pass3TransportResult(
                True,
                final_tc,
                {
                    "over_capacity_segments": 0,
                    "bottleneck_count": 0,
                    "commit_reason": COMMIT_REASON_GUARDED_ATOMIC,
                    "gain": gain_atomic,
                },
            )
            guarded_committed_outcome = True
        else:
            final_tc = _p3e3_rollback_guarded_transport_cells(
                known_good_transport_snapshot=known_good_transport_snapshot,
            )
            result = Pass3TransportResult(
                greedy_result.committed,
                final_tc,
                dict(greedy_result.metrics),
            )
            guarded_committed_outcome = False
            rollback_performed = True
            rollback_reason = post_fail_reason or P3E3_REJECT_VALIDATION
    else:
        result = greedy_result

    if guarded_on:
        p3e3_trace.update(
            {
                "p3e3_guarded_commit_committed": guarded_committed_outcome,
                "p3e3_guarded_committed": guarded_committed_outcome,
                "p3e3_guarded_commit_rollback_performed": rollback_performed,
                "p3e3_guarded_commit_rollback_reason": rollback_reason,
                "p3e3_guarded_commit_mode": "atomic_candidate_swap" if should_commit else None,
                "p3e3_guarded_known_good_transport_cell_count": len(known_good_transport_snapshot),
                "p3e3_guarded_post_commit_validation_passed": post_commit_passed,
            }
        )

    new_map = mining_map_after_transport_reconstruction(
        mining_map,
        result.transport_cells,
        target_role=wr,
    )
    after_transport_count = len(result.transport_cells)
    after_internal_transport_count = len(set(result.transport_cells) & asteroid_set)
    pass3_transport_cells_removed_total = max(0, before_transport_count - after_transport_count)
    pass3_internal_transport_saved = max(
        0, before_internal_transport_count - after_internal_transport_count
    )
    trace = {
        "pass3_skipped": False,
        "pass3_committed": result.committed,
        "pass3_greedy_committed": greedy_result.committed,
        **shadow_trace,
        **p3e3_trace,
        "before_transport_count": before_transport_count,
        "after_transport_count": after_transport_count,
        "before_internal_transport_count": before_internal_transport_count,
        "after_internal_transport_count": after_internal_transport_count,
        "pass3_transport_cells_removed_total": pass3_transport_cells_removed_total,
        "pass3_internal_transport_saved": pass3_internal_transport_saved,
        **result.metrics,
    }
    return new_map, result, trace


__all__ = [
    "MAX_ROUTE_LENGTH_RATIO",
    "P3E3_ATOMIC_SKIPPED_SHADOW_LEX_INCOMPLETE",
    "P3E3GuardedCommitCandidate",
    "P3E3_REJECT_CONNECTIVITY",
    "P3E3_REJECT_FIXED_STUB_REMOVAL",
    "P3E3_REJECT_HARD_PROTECTED_CORRIDOR",
    "P3E3_REJECT_NO_REPLACEMENT_ROUTE",
    "P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE",
    "P3E3_REJECT_ROUTE_LENGTH_RATIO",
    "Pass3TransportResult",
    "_p3e3_atomic_trace_from_dto",
    "_p3e3_build_atomic_candidate_map",
    "_p3e3_rollback_guarded_transport_cells",
    "_p3e3_route_length_ratio_allowed",
    "_p3e3_run_atomic_candidate_phase",
    "_p3e3_should_commit_guarded_candidate",
    "mining_map_after_transport_reconstruction",
    "mining_priority_route_cell_cost",
    "p3e2_pass3_summary_placeholder",
    "p3e3_pass3_summary_placeholder",
    "placement_stub_route_probe_path",
    "placement_stub_route_to_trunk_feasible",
    "reconstruct_mining_priority_transport",
    "run_pass3_transport_minimization_from_maps",
    "transport_connects_outlets_to_anchor",
]
