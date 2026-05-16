"""Existing-layout inspection: ORM read, replay frames, optional cell snapshot (A6)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_EXISTING_LAYOUT_ATTACHMENT_ANALYZED,
    EVENT_TYPE_EXISTING_LAYOUT_BEGIN,
    EVENT_TYPE_EXISTING_LAYOUT_EQUIPMENT_INDEXED,
    EVENT_TYPE_EXISTING_LAYOUT_HINTS_GENERATED,
    EVENT_TYPE_EXISTING_LAYOUT_ISSUES_DETECTED,
    EVENT_TYPE_EXISTING_LAYOUT_TRANSPORT_COMPONENTS_INDEXED,
)
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
)
from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    ExistingEquipmentDTO,
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


def _equipment_cell_overlay(eq: ExistingEquipmentDTO) -> dict[str, Any]:
    return {
        "x": eq.x,
        "y": eq.y,
        "layer": eq.layer,
        "rotation": eq.rotation,
        "cell_kind": eq.cell_kind,
        "transport_kind": eq.transport_kind,
        "tile_type": eq.tile_type,
        "equipment_id": eq.equipment_id,
        "role": "equipment",
    }


def record_existing_layout_inspection_frames(
    track_id: int,
    inspection: ExistingLayoutInspectionDTO,
) -> list[SnapshotFrameDTO]:
    """Append six ``existing_layout.*`` replay frames (UI-only; never solver input)."""

    recorder = ReplayRecorder(int(track_id))
    phase = "existing_layout"

    summary = dict(inspection.summary_json)
    begin_metrics: dict[str, Any] = {
        "transport_component_count": summary.get("transport_component_count"),
        "equipment_count": summary.get("equipment_count"),
        "issue_count": summary.get("issue_count"),
    }
    ev_begin = SnapshotEventDTO(
        event_key="existing_layout.begin",
        phase=phase,
        phase_step="begin",
        event_type=EVENT_TYPE_EXISTING_LAYOUT_BEGIN,
        title="Existing layout inspection started",
        description="Read-only analysis of decoded top-level cells (no nested unfold).",
        after_state_json={
            "summary_json": summary,
            "transport_components_by_kind": summary.get("transport_components_by_kind"),
        },
        cell_overlay_json={},
        metrics_json=begin_metrics,
        is_decision_point=True,
    )

    transport_overlay: dict[str, Any] = {
        "components": [
            {
                "component_id": c.component_id,
                "transport_kind": c.transport_kind,
                "cells": [
                    {
                        **cell,
                        "overlay_role": "transport",
                        "is_main_component": cell.get("role") == "main",
                    }
                    for cell in c.cells_json
                ],
            }
            for c in inspection.transport_components
        ]
    }
    ev_transport = SnapshotEventDTO(
        event_key="existing_layout.transport_components_indexed",
        phase=phase,
        phase_step="transport",
        event_type=EVENT_TYPE_EXISTING_LAYOUT_TRANSPORT_COMPONENTS_INDEXED,
        title="Transport components indexed",
        description="SpacePipe / SpaceBelt cells grouped by transport_kind (4-neighbor).",
        after_state_json={
            "component_count": len(inspection.transport_components),
            "components_summary": [
                {
                    "component_id": c.component_id,
                    "transport_kind": c.transport_kind,
                    "cell_count": c.cell_count,
                    "touches_bbox_edge": c.touches_bbox_edge,
                }
                for c in inspection.transport_components
            ],
        },
        cell_overlay_json=transport_overlay,
        metrics_json={"components": len(inspection.transport_components)},
        is_decision_point=True,
    )

    equip_cells = [_equipment_cell_overlay(eq) for eq in inspection.equipment]
    ev_equip = SnapshotEventDTO(
        event_key="existing_layout.equipment_indexed",
        phase=phase,
        phase_step="equipment",
        event_type=EVENT_TYPE_EXISTING_LAYOUT_EQUIPMENT_INDEXED,
        title="Equipment indexed",
        description="Miner and extension cells from top-level BP.Entries.",
        after_state_json={"equipment_count": len(inspection.equipment)},
        cell_overlay_json={"equipment_cells": equip_cells},
        metrics_json={"equipment_count": len(inspection.equipment)},
        is_decision_point=True,
    )

    attach_overlay_cells: list[dict[str, Any]] = list(equip_cells)
    for att in inspection.attachments:
        for cell in att.adjacent_transport_cells_json:
            row = dict(cell)
            row["overlay_role"] = "adjacent_transport"
            row["for_equipment_id"] = att.equipment_id
            attach_overlay_cells.append(row)
    ev_attach = SnapshotEventDTO(
        event_key="existing_layout.attachment_analyzed",
        phase=phase,
        phase_step="attachment",
        event_type=EVENT_TYPE_EXISTING_LAYOUT_ATTACHMENT_ANALYZED,
        title="Equipment–transport attachment analyzed",
        description="4-neighbor adjacency to indexed transport components.",
        after_state_json={"attachments": [asdict(a) for a in inspection.attachments]},
        cell_overlay_json={"cells": attach_overlay_cells},
        metrics_json={"attachment_rows": len(inspection.attachments)},
        is_decision_point=True,
    )

    issue_cells: list[dict[str, Any]] = []
    for iss in inspection.issues:
        for cell in iss.cells_json:
            issue_cells.append(
                {
                    **cell,
                    "overlay_role": "issue",
                    "issue_code": iss.issue_code,
                    "severity": iss.severity,
                    "equipment_id": iss.equipment_id,
                }
            )
    ev_issues = SnapshotEventDTO(
        event_key="existing_layout.issues_detected",
        phase=phase,
        phase_step="issues",
        event_type=EVENT_TYPE_EXISTING_LAYOUT_ISSUES_DETECTED,
        title="Layout issues detected",
        description="Inspection issues (UI only; not solver input).",
        after_state_json={"issues": [asdict(i) for i in inspection.issues]},
        cell_overlay_json={"issue_cells": issue_cells},
        metrics_json={"issue_count": len(inspection.issues)},
        is_decision_point=True,
    )

    hints = dict(inspection.hints_json)
    main_cand = hints.get("main_component_candidate") or {}
    cleanup = hints.get("cleanup_candidate_cells") or []
    ev_hints = SnapshotEventDTO(
        event_key="existing_layout.hints_generated",
        phase=phase,
        phase_step="hints",
        event_type=EVENT_TYPE_EXISTING_LAYOUT_HINTS_GENERATED,
        title="Inspection hints generated",
        description="Main component candidates and cleanup overlay (UI only).",
        after_state_json={"hints_json": hints},
        cell_overlay_json={
            "main_component_candidate": main_cand,
            "cleanup_candidate_cells": cleanup,
        },
        metrics_json={"cleanup_cell_count": len(cleanup)},
        is_decision_point=True,
    )

    return recorder.record_many([ev_begin, ev_transport, ev_equip, ev_attach, ev_issues, ev_hints])


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
