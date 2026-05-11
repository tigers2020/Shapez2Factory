"""Replay UI frames: map ``solver_timeline`` rows to replay ``events`` slices (STEP10 bridge).

Layout maps stay on ``solver_timeline[i].mining_map``; ``ui_frames`` carries indices,
computation_cycle bounds, Pass3 snapshot metadata, and overlay hints (contract v4+).
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_PHASE_VALIDATION_RECOVERY,
    SOLVER_FRAME_INIT,
    SOLVER_FRAME_PASS1_OUTER,
    SOLVER_FRAME_PASS2_INTERNAL,
    SOLVER_FRAME_PASS3_TRANSPORT,
    SOLVER_FRAME_STEP4_ROUTING,
    SOLVER_FRAME_VALIDATE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_corridors import (  # noqa: E501
    effective_routing_state_at_timeline_index,
    protected_corridors_overlay_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
)

# Timeline frame id -> replay event ``phase`` strings contributing to that frame.
_UI_COMPUTATION_CYCLE_STRIDE = 10

_OVERLAY_KINDS: frozenset[str] = frozenset(
    {
        SolverMutationEventKind.RECOVERY_BRANCH.value,
        SolverMutationEventKind.ROLLBACK.value,
        SolverMutationEventKind.ROUTE_REPLACED.value,
    }
)

_FRAME_ID_TO_EVENT_PHASES: dict[str, tuple[str, ...]] = {
    SOLVER_FRAME_INIT: (),
    SOLVER_FRAME_PASS1_OUTER: (),
    SOLVER_FRAME_PASS2_INTERNAL: ("pass12",),
    SOLVER_FRAME_STEP4_ROUTING: ("step4",),
    SOLVER_FRAME_PASS3_TRANSPORT: ("pass3", "p4_reclaim"),
    # P5 orchestrator emits ``recovery_branch`` with ``phase="validation_recovery"`` (see
    # ``recovery_orchestrator``); attach to the final validation timeline row for STEP10 UI.
    SOLVER_FRAME_VALIDATE: (RECOVERY_PHASE_VALIDATION_RECOVERY,),
}


def build_replay_ui_frames(
    *,
    solver_timeline: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """One UI meta row per ``solver_timeline`` entry; ``event_indices`` reference ``events``."""

    phase_to_indices: dict[str, list[int]] = {}
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            continue
        ph = ev.get("phase")
        if isinstance(ph, str):
            phase_to_indices.setdefault(ph, []).append(i)

    out: list[dict[str, Any]] = []
    for idx, frame in enumerate(solver_timeline):
        if not isinstance(frame, dict):
            out.append(_empty_ui_frame(timeline_index=idx, timeline_frame_id=""))
            continue
        fid = str(frame.get("id") or "")
        phases = _FRAME_ID_TO_EVENT_PHASES.get(fid, ())
        indices: list[int] = []
        for p in phases:
            indices.extend(phase_to_indices.get(p, []))
        indices = sorted(set(indices))

        cycles: list[int] = []
        for j in indices:
            cyc = events[j].get("computation_cycle") if isinstance(events[j], dict) else None
            if isinstance(cyc, int):
                cycles.append(cyc)
        c_start = min(cycles) if cycles else None
        c_end = max(cycles) if cycles else None

        tick_start: int | None = None
        tick_end: int | None = None
        if isinstance(c_start, int) and isinstance(c_end, int):
            tick_start = (c_start - 1) // _UI_COMPUTATION_CYCLE_STRIDE + 1
            tick_end = (c_end - 1) // _UI_COMPUTATION_CYCLE_STRIDE + 1

        overlay_indices = sorted(
            j
            for j in indices
            if isinstance(events[j], dict) and events[j].get("kind") in _OVERLAY_KINDS
        )

        p3_snaps: list[dict[str, Any]] = []
        for j in indices:
            ev = events[j]
            if not isinstance(ev, dict):
                continue
            if ev.get("kind") != SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value:
                continue
            pl = ev.get("payload")
            if not isinstance(pl, dict):
                continue
            marker = pl.get("marker")
            h = pl.get("layout_state_sha256")
            tid = pl.get("transaction_id")
            if isinstance(marker, str) and isinstance(h, str):
                row: dict[str, Any] = {"marker": marker, "layout_state_sha256": h}
                if isinstance(tid, str):
                    row["transaction_id"] = tid
                p3_snaps.append(row)

        rs_eff = effective_routing_state_at_timeline_index(solver_timeline, idx)
        pc_overlay = protected_corridors_overlay_from_routing_state(rs_eff)

        out.append(
            {
                "timeline_frame_id": fid,
                "timeline_index": idx,
                "event_indices": indices,
                "computation_cycle_start": c_start,
                "computation_cycle_end": c_end,
                "computation_cycle_ui_stride": _UI_COMPUTATION_CYCLE_STRIDE,
                "computation_cycle_ui_tick_start": tick_start,
                "computation_cycle_ui_tick_end": tick_end,
                "primary_for_step10_ui": True,
                "overlay_event_indices": overlay_indices,
                "pass3_layout_snapshots": p3_snaps,
                "protected_corridors": pc_overlay,
            }
        )
    return out


def _empty_ui_frame(*, timeline_index: int, timeline_frame_id: str) -> dict[str, Any]:
    return {
        "timeline_frame_id": timeline_frame_id,
        "timeline_index": timeline_index,
        "event_indices": [],
        "computation_cycle_start": None,
        "computation_cycle_end": None,
        "computation_cycle_ui_stride": _UI_COMPUTATION_CYCLE_STRIDE,
        "computation_cycle_ui_tick_start": None,
        "computation_cycle_ui_tick_end": None,
        "primary_for_step10_ui": True,
        "overlay_event_indices": [],
        "pass3_layout_snapshots": [],
        "protected_corridors": protected_corridors_overlay_from_routing_state(None),
    }


__all__ = ["build_replay_ui_frames"]
