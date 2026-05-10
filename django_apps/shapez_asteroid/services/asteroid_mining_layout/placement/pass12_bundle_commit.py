"""Pass1/Pass2 bundle commit gate (Stabilization-P1).

Placement must mutate ``transport_cells`` / ``blocked_cells`` (and Pass1 extension
metadata on ``Pass12LayoutScratch``) only through ``try_commit_pass1_bundle`` and
``try_commit_pass2_bundle`` so a failed stub→external probe never leaves new occupied
bodies or stub transport on the scratch layout.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    PASS12_TRY_COMMIT_PASS1_BUNDLE_TRACE_LOCATION,
    PASS12_TRY_COMMIT_PASS2_BUNDLE_TRACE_LOCATION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_contracts import (
    Pass12BundleCandidate,
    Pass12LayoutScratch,
    Pass12ScratchBaseline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_route_probe import (  # noqa: E501
    bundle_route_probe_or_reject,
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
    "restore_pass12_scratch",
    "snapshot_pass12_scratch",
    "try_commit_pass1_bundle",
    "try_commit_pass2_bundle",
]


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
    )


def try_commit_pass2_bundle(
    state: Pass12LayoutScratch,
    candidate: Pass12BundleCandidate,
    *,
    is_external: Callable[[Coord], bool],
    bundle_hint: dict[str, Any] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
) -> bool:
    """Same gate as Pass1 for spine/merge transport bundles."""

    return _commit_after_probe(
        state,
        candidate,
        is_external=is_external,
        trace_location=_PASS2_TRACE,
        bundle_hint=bundle_hint,
        replay_events=replay_events,
    )


def _commit_after_probe(
    state: Pass12LayoutScratch,
    candidate: Pass12BundleCandidate,
    *,
    is_external: Callable[[Coord], bool],
    trace_location: str,
    bundle_hint: dict[str, Any] | None,
    replay_events: list[dict[str, Any]] | None,
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
            trace_bundle_reject_invalid_stub(trace_location, payload)
            return False
        if not bundle_route_probe_or_reject(
            candidate.stub_cell,
            transport_cells=transport_after,
            blocked_cells=blocked_after,
            is_external=is_external,
            trace_location=trace_location,
            bundle_hint=bundle_hint,
            pass1_allow_cheap_escape=(trace_location == _PASS1_TRACE),
            p1_cheap_void_cells=candidate.p1_cheap_void_cells,
        ):
            return False
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
            if replay_events is not None:
                replay_events.append(
                    {
                        "kind": SolverMutationEventKind.PASS12_BUNDLE_COMMIT.value,
                        "phase": "pass12",
                        "payload": {
                            "placement_id": pid,
                            "placement_pass": candidate.placement_pass,
                            "trace_location": trace_location,
                        },
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
