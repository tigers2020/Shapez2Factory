"""Existing-layout inspection: ORM read, replay frames, optional cell snapshot (A6)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.trace import ReconstructionTraceCollector
from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR,
    EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
)
from django_apps.asteroid_lab.replay.reconstruction_frames import build_reconstruction_replay_events
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    build_cleanup_and_reconstruction_rows,
    diff_maps,
    filter_issue_cells_for_full_map,
    issue_overlay_cells,
    rows_from_cells,
    snapshot_summary_from_rows,
)
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
)
from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    ExistingLayoutInspectionDTO,
    SnapshotEventDTO,
    SnapshotFrameDTO,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder
from django_apps.asteroid_lab.snapshots.existing_layout_inspection import inspect_existing_layout


def build_existing_layout_inspection_from_snapshot(
    snapshot: DecodedBlueprintSnapshotDTO,
) -> ExistingLayoutInspectionDTO:
    """Run pure inspection on an A5 snapshot (no ORM, no replay reads, no reconstruction)."""

    return inspect_existing_layout(snapshot)


def build_existing_layout_inspection_from_input(map_input_id: int) -> ExistingLayoutInspectionDTO:
    """Load ``AsteroidMapInput.decoded_json``, build A5 snapshot, inspect (does not mutate JSON)."""

    snap = build_decoded_blueprint_snapshot_from_input(int(map_input_id))
    return inspect_existing_layout(snap)


def record_existing_layout_inspection_frames(
    track_id: int,
    inspection: ExistingLayoutInspectionDTO,
) -> list[SnapshotFrameDTO]:
    """Append cleanup frames plus stepwise reconstruction replay (UI-only; never solver input)."""

    if inspection.map_input_id is None:
        msg = "ExistingLayoutInspectionDTO.map_input_id is required for snapshot replay"
        raise ValueError(msg)

    snap = build_decoded_blueprint_snapshot_from_input(int(inspection.map_input_id))
    _, row_transport, row_extractor, row_extension, _, _ = build_cleanup_and_reconstruction_rows(
        snap
    )

    cleanup = load_cleanup_result(snap)
    collector = ReconstructionTraceCollector()
    recon = run_topology_reconstruction(cleanup, trace_collector=collector)
    row_recon = rows_from_cells(recon.cells)
    recon_extra = {**dict(cleanup.summary_json), **dict(recon.summary_json)}

    recorder = ReplayRecorder(int(track_id))
    phase = "layout_cleanup"
    ins_summary = dict(inspection.summary_json)

    ev_transport = SnapshotEventDTO(
        event_key="step1_cleanup_transport",
        phase=phase,
        phase_step="transport",
        event_type=EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
        title="After transport cleanup",
        description=("Transport already stripped in step0; this frame marks the cleanup baseline."),
        after_state_json={"inspection_summary": ins_summary},
        cell_overlay_json={"cells": row_transport},
        metrics_json=snapshot_summary_from_rows(row_transport),
        is_decision_point=True,
        full_map=list(row_transport),
        diff=diff_maps(row_transport, row_transport),
        summary=snapshot_summary_from_rows(row_transport),
    )

    ev_extractor = SnapshotEventDTO(
        event_key="step2_cleanup_extractor",
        phase=phase,
        phase_step="extractor",
        event_type=EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR,
        title="After extractor cleanup",
        description="Full map with miners removed; underlying field visible where applicable.",
        after_state_json={"inspection_summary": ins_summary},
        cell_overlay_json={"cells": row_extractor},
        metrics_json=snapshot_summary_from_rows(row_extractor),
        is_decision_point=True,
        full_map=list(row_extractor),
        diff=diff_maps(row_transport, row_extractor),
        summary=snapshot_summary_from_rows(row_extractor),
    )

    ev_extension = SnapshotEventDTO(
        event_key="step3_cleanup_extension",
        phase=phase,
        phase_step="extension",
        event_type=EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION,
        title="After extension cleanup",
        description="Full map with miner extensions removed.",
        after_state_json={"inspection_summary": ins_summary},
        cell_overlay_json={"cells": row_extension},
        metrics_json=snapshot_summary_from_rows(row_extension),
        is_decision_point=True,
        full_map=list(row_extension),
        diff=diff_maps(row_extractor, row_extension),
        summary=snapshot_summary_from_rows(row_extension),
    )

    issues_payload = [asdict(i) for i in inspection.issues]
    hints = dict(inspection.hints_json)
    i_cells_raw = issue_overlay_cells(inspection)
    i_cells = filter_issue_cells_for_full_map(i_cells_raw, row_recon)
    recon_summary = snapshot_summary_from_rows(row_recon)
    recon_summary.update(recon_extra)
    recon_summary["inspection_issue_count"] = len(inspection.issues)
    recon_summary["visible_issue_cell_count"] = len(i_cells)
    recon_summary["inspection"] = {
        "summary_json": ins_summary,
        "issues": issues_payload,
        "hints_json": hints,
        "attachments": [asdict(a) for a in inspection.attachments],
        "transport_components": [
            {
                "component_id": c.component_id,
                "transport_kind": c.transport_kind,
                "cell_count": c.cell_count,
                "touches_bbox_edge": c.touches_bbox_edge,
            }
            for c in inspection.transport_components
        ],
    }

    recon_events = build_reconstruction_replay_events(
        structural_rows=list(row_extension),
        cleanup=cleanup,
        recon=recon,
        trace_events=collector.events,
        recon_summary=dict(recon_summary),
        hints=hints,
        final_issue_cells=i_cells,
    )

    return recorder.record_many([ev_transport, ev_extractor, ev_extension, *recon_events])


def persist_existing_layout_inspection_snapshot(
    project_id: int,
    map_input_id: int,
    inspection: ExistingLayoutInspectionDTO,
) -> int:
    """Persist inspection on :class:`AsteroidCellSnapshot` JSON fields (no migration).

    ``AsteroidCellSnapshot`` already carries ``cell_grid_json`` / ``overlay_json``; this stores
    ``layer="existing_layout_inspection"`` for UI/cache. Never solver algorithm input.
    """

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)
    if int(inp.project_id) != int(project_id):
        msg = "map_input.project_id does not match project_id"
        raise ValueError(msg)

    overlay: dict[str, Any] = {
        "schema": "asteroid_lab_existing_layout_inspection_v1",
        "summary_json": dict(inspection.summary_json),
        "hints_json": dict(inspection.hints_json),
        "issue_codes": [i.issue_code for i in inspection.issues],
    }
    grid: dict[str, Any] = {
        "inspection": asdict(inspection),
    }
    row = m.AsteroidCellSnapshot.objects.create(
        map_input=inp,
        layer="existing_layout_inspection",
        cell_grid_json=grid,
        overlay_json=overlay,
    )
    return int(row.pk)


__all__ = [
    "build_existing_layout_inspection_from_input",
    "build_existing_layout_inspection_from_snapshot",
    "persist_existing_layout_inspection_snapshot",
    "record_existing_layout_inspection_frames",
]
