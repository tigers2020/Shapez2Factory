"""Pass1/Pass2 bundle commit gate (Stabilization-P1).

Placement must mutate ``transport_cells`` / ``blocked_cells`` (and Pass1 extension
metadata on ``Pass12LayoutScratch``) only through ``try_commit_pass1_bundle`` and
``try_commit_pass2_bundle`` so a failed Pass1 stub→external probe never leaves new occupied
bodies or stub transport on the scratch layout.

Pass2 with ``Pass2RouteProbePack`` may still commit ``PROVISIONAL_PLACED`` when the route is
uncertain (STEP4 merge-aware routing decides later); Pass1 behavior is unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    rotation_r_for_output_direction,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    PASS12_TRY_COMMIT_PASS1_BUNDLE_TRACE_LOCATION,
    PASS12_TRY_COMMIT_PASS2_BUNDLE_TRACE_LOCATION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extension_topology import (  # noqa: E501
    rotation_r_for_extension_facing_parent,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_contracts import (
    Pass12BundleCandidate,
    Pass12LayoutScratch,
    Pass12ScratchBaseline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_route_probe import (  # noqa: E501
    Pass2RouteProbePack,
    build_pass2_step4_aligned_routing_goals,
    bundle_route_probe_or_reject,
    pass2_bundle_route_probe_decision,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    make_placement_id,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_bundle_reject_invalid_stub,
)

_PASS1_TRACE = PASS12_TRY_COMMIT_PASS1_BUNDLE_TRACE_LOCATION
_PASS2_TRACE = PASS12_TRY_COMMIT_PASS2_BUNDLE_TRACE_LOCATION

__all__ = [
    "Pass12BundleCandidate",
    "Pass12LayoutScratch",
    "Pass12ScratchBaseline",
    "Pass2RouteProbePack",
    "restore_pass12_scratch",
    "snapshot_pass12_scratch",
    "try_commit_pass1_bundle",
    "try_commit_pass2_bundle",
]


def _coord_payload(c: Coord | None) -> list[int] | None:
    if c is None:
        return None
    return [int(c[0]), int(c[1])]


def _pass12_commit_replay_payload(
    *,
    pid: str,
    state: Pass12LayoutScratch,
    candidate: Pass12BundleCandidate,
    trace_location: str,
) -> dict[str, Any]:
    output_dir = candidate.extractor_output_dir
    extension_cells = []
    for c, edx, edy in sorted(candidate.extension_facings, key=lambda row: (row[0][1], row[0][0])):
        extension_cells.append(
            {
                "x": int(c[0]),
                "y": int(c[1]),
                "facing_parent": [int(edx), int(edy)],
                "r": rotation_r_for_extension_facing_parent((edx, edy)),
            }
        )
    return {
        "placement_id": pid,
        "placement_pass": candidate.placement_pass,
        "trace_location": trace_location,
        "transport_kind": state.transport_kind,
        "extractor_cell": _coord_payload(candidate.extractor_cell),
        "extractor_output_dir": [int(output_dir[0]), int(output_dir[1])] if output_dir else None,
        "extractor_r": (
            rotation_r_for_output_direction(output_dir[0], output_dir[1])
            if output_dir is not None
            else None
        ),
        "extension_cells": extension_cells,
        "stub_cell": _coord_payload(candidate.stub_cell),
        "new_transport_cells": [
            _coord_payload(c) for c in sorted(candidate.new_transport, key=lambda t: (t[1], t[0]))
        ],
    }


def snapshot_pass12_scratch(state: Pass12LayoutScratch) -> Pass12ScratchBaseline:
    facings_items = frozenset((c, dx, dy) for c, (dx, dy) in state.extension_facings.items())
    out_dirs = frozenset((c, dx, dy) for c, (dx, dy) in state.extractor_output_dirs.items())
    return Pass12ScratchBaseline(
        transport_cells=frozenset(state.transport_cells),
        blocked_cells=frozenset(state.blocked_cells),
        extractor_cells=frozenset(state.extractor_cells),
        extension_facings=facings_items,
        extractor_output_dirs=out_dirs,
        transport_kind=state.transport_kind,
        next_placement_seq=state.next_placement_seq,
        placement_records=dict(state.placement_records),
        preserved_mining_row_overrides=dict(state.preserved_mining_row_overrides),
    )


def restore_pass12_scratch(state: Pass12LayoutScratch, baseline: Pass12ScratchBaseline) -> None:
    state.transport_cells = set(baseline.transport_cells)
    state.blocked_cells = set(baseline.blocked_cells)
    state.extractor_cells = set(baseline.extractor_cells)
    state.extension_facings = {c: (dx, dy) for c, dx, dy in baseline.extension_facings}
    state.extractor_output_dirs = {c: (dx, dy) for c, dx, dy in baseline.extractor_output_dirs}
    state.transport_kind = baseline.transport_kind
    state.next_placement_seq = baseline.next_placement_seq
    state.placement_records = dict(baseline.placement_records)
    state.preserved_mining_row_overrides = dict(baseline.preserved_mining_row_overrides)


def try_commit_pass1_bundle(
    state: Pass12LayoutScratch,
    candidate: Pass12BundleCandidate,
    *,
    is_external: Callable[[Coord], bool],
    bundle_hint: dict[str, Any] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
) -> bool:
    """Probe on hypothetical layout; merge candidate into ``state`` only when routed.

    P1-A/P1-B route probe is a **placement commit safety gate** only; it does not
    replace STEP4 final merge-aware routing.
    """

    return _commit_after_probe(
        state,
        candidate,
        is_external=is_external,
        trace_location=_PASS1_TRACE,
        bundle_hint=bundle_hint,
        replay_events=replay_events,
        adjacent_preserve_trunk_baseline_cells=None,
        pass2_route_probe_pack=None,
    )


def try_commit_pass2_bundle(
    state: Pass12LayoutScratch,
    candidate: Pass12BundleCandidate,
    *,
    is_external: Callable[[Coord], bool],
    bundle_hint: dict[str, Any] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
    adjacent_preserve_trunk_baseline_cells: frozenset[Coord] | None = None,
    pass2_route_probe_pack: Pass2RouteProbePack | None = None,
) -> bool:
    """Same gate as Pass1 for spine/merge transport bundles."""

    return _commit_after_probe(
        state,
        candidate,
        is_external=is_external,
        trace_location=_PASS2_TRACE,
        bundle_hint=bundle_hint,
        replay_events=replay_events,
        adjacent_preserve_trunk_baseline_cells=adjacent_preserve_trunk_baseline_cells,
        pass2_route_probe_pack=pass2_route_probe_pack,
    )


def _commit_after_probe(
    state: Pass12LayoutScratch,
    candidate: Pass12BundleCandidate,
    *,
    is_external: Callable[[Coord], bool],
    trace_location: str,
    bundle_hint: dict[str, Any] | None,
    replay_events: list[dict[str, Any]] | None,
    adjacent_preserve_trunk_baseline_cells: frozenset[Coord] | None,
    pass2_route_probe_pack: Pass2RouteProbePack | None,
) -> bool:
    """Pass1/Pass2 bundle을 route probe 성공 후에만 commit한다.

        route probe gate 본체이며 STEP4 final merge-aware routing은 아니다 (§3.3, §9).

    상세: documents/Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md"""
    baseline = snapshot_pass12_scratch(state)
    try:
        transport_after = frozenset(state.transport_cells | set(candidate.new_transport))
        blocked_after = frozenset(state.blocked_cells | set(candidate.blocked_cells))
        if candidate.stub_cell not in transport_after:
            payload: dict[str, Any] = dict(bundle_hint or {})
            payload["reason"] = "stub_cell_missing_from_merged_transport"
            payload["stub_cell"] = candidate.stub_cell
            payload["route_probe_context"] = {
                "transport_cell_count": len(transport_after),
                "blocked_cell_count": len(blocked_after),
            }
            trace_bundle_reject_invalid_stub(trace_location, payload)
            if trace_location == _PASS2_TRACE and pass2_route_probe_pack is not None:
                sink = pass2_route_probe_pack.stats_sink
                sink["pass2_hard_geometry_reject_count"] = (
                    int(sink.get("pass2_hard_geometry_reject_count", 0)) + 1
                )
            return False
        pass2_outcome: str | None = None
        if trace_location == _PASS2_TRACE and pass2_route_probe_pack is not None:
            pack = pass2_route_probe_pack
            goals, gkind, gn, goal_trace = build_pass2_step4_aligned_routing_goals(
                transport_kind=state.transport_kind,
                mineable=pack.mineable,
                asteroid=pack.asteroid,
                cells=pack.cells,
                is_external=is_external,
                existing_layout_analysis=pack.existing_layout_analysis,
                transport_cells_before=frozenset(baseline.transport_cells),
                transport_cells_probe=transport_after,
                blocked_for_probe=blocked_after,
                stats_sink=pack.stats_sink,
            )
            p2_out, _diag = pass2_bundle_route_probe_decision(
                candidate.stub_cell,
                transport_cells=transport_after,
                blocked_cells=blocked_after,
                is_external=is_external,
                routing_goal_cells=goals,
                goal_set_kind=gkind,
                goal_count=gn,
                adjacent_preserve_trunk_baseline_cells=adjacent_preserve_trunk_baseline_cells,
                stats_sink=pack.stats_sink,
                goal_build_trace=goal_trace,
            )
            pass2_outcome = p2_out
        else:
            if not bundle_route_probe_or_reject(
                candidate.stub_cell,
                transport_cells=transport_after,
                blocked_cells=blocked_after,
                is_external=is_external,
                trace_location=trace_location,
                bundle_hint=bundle_hint,
                pass1_allow_cheap_escape=(trace_location == _PASS1_TRACE),
                p1_cheap_void_cells=candidate.p1_cheap_void_cells,
                pass2_adjacent_preserve_trunk_baseline_cells=(
                    adjacent_preserve_trunk_baseline_cells
                    if trace_location == _PASS2_TRACE
                    else None
                ),
            ):
                return False
            pass2_outcome = "routed"
        state.transport_cells |= set(candidate.new_transport)
        state.blocked_cells |= set(candidate.blocked_cells)
        if candidate.extractor_cell is not None:
            state.extractor_cells.add(candidate.extractor_cell)
            if candidate.extractor_output_dir is not None:
                ec = candidate.extractor_cell
                state.extractor_output_dirs[ec] = candidate.extractor_output_dir
            for c, edx, edy in candidate.extension_facings:
                state.extension_facings[c] = (edx, edy)
        if candidate.extractor_cell is not None:
            state.next_placement_seq += 1
            pid = make_placement_id(candidate.placement_pass, state.next_placement_seq)
            ext_cells = tuple(
                sorted(
                    (c for c, _edx, _edy in candidate.extension_facings), key=lambda t: (t[1], t[0])
                )
            )
            state.placement_records[pid] = PlacementCommitRecord(
                placement_id=pid,
                placement_pass=candidate.placement_pass,
                extractor_cell=candidate.extractor_cell,
                extension_cells=ext_cells,
                stub_cell=candidate.stub_cell,
                transport_kind=state.transport_kind,
                state=PlacementCommitState.PROVISIONAL_PLACED,
            )
            if (
                trace_location == _PASS2_TRACE
                and pass2_route_probe_pack is not None
                and pass2_outcome == "uncertain"
            ):
                sink = pass2_route_probe_pack.stats_sink
                sink["pass2_provisional_unrouted_count"] = (
                    int(sink.get("pass2_provisional_unrouted_count", 0)) + 1
                )
            if replay_events is not None:
                replay_events.append(
                    {
                        "kind": SolverMutationEventKind.PASS12_BUNDLE_COMMIT.value,
                        "phase": "pass12",
                        "payload": _pass12_commit_replay_payload(
                            pid=pid,
                            state=state,
                            candidate=candidate,
                            trace_location=trace_location,
                        ),
                    }
                )
                replay_events.append(
                    {
                        "kind": SolverMutationEventKind.PLACEMENT_STATE_CHANGED.value,
                        "phase": "pass12",
                        "payload": {
                            "placement_id": pid,
                            "state": PlacementCommitState.PROVISIONAL_PLACED.value,
                        },
                    }
                )
        return True
    except BaseException:
        restore_pass12_scratch(state, baseline)
        raise
