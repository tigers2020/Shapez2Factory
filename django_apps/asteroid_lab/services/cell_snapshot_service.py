"""Decoded blueprint snapshot: ORM read, replay frames, optional ``AsteroidCellSnapshot`` row."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_DECODE_NORMALIZED
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    decode_snapshot_summary,
    rows_from_cells,
)
from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
    SnapshotEventDTO,
    SnapshotFrameDTO,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)


def build_decoded_blueprint_snapshot_from_input(map_input_id: int) -> DecodedBlueprintSnapshotDTO:
    """Load ``AsteroidMapInput.decoded_json`` and build a pure snapshot DTO."""

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)
    raw = inp.decoded_json
    decoded: dict[str, Any] = dict(raw) if isinstance(raw, dict) else {}
    return build_decoded_blueprint_snapshot(
        decoded,
        project_id=int(inp.project_id),
        map_input_id=int(inp.id),
    )


def _overlay_cell_dict(c: DecodedCellDTO) -> dict[str, Any]:
    return {
        "x": c.x,
        "y": c.y,
        "layer": c.layer,
        "rotation": c.rotation,
        "cell_kind": c.cell_kind,
        "transport_kind": c.transport_kind,
        "tile_type": c.tile_type,
    }


def record_decoded_snapshot_frames(
    track_id: int,
    snapshot: DecodedBlueprintSnapshotDTO,
) -> list[SnapshotFrameDTO]:
    """Append one decode replay frame: full decoded blueprint map snapshot (UI-only artifact)."""

    recorder = ReplayRecorder(int(track_id))
    bv = snapshot.binary_version
    full_map = rows_from_cells(snapshot.cells)
    norm_metrics: dict[str, Any] = {
        "binary_version": bv,
        "blueprint_type": snapshot.blueprint_type,
        "entry_count": snapshot.entry_count,
        "cell_kind_counts": dict(snapshot.cell_kind_counts_json),
        "transport_kind_counts": dict(snapshot.transport_kind_counts_json),
        "bbox": dict(snapshot.bbox_json),
    }
    frame_summary = decode_snapshot_summary(snapshot)

    ev_decode = SnapshotEventDTO(
        event_key="step0_decode",
        phase="decode",
        phase_step="normalized",
        event_type=EVENT_TYPE_DECODE_NORMALIZED,
        title="Decoded blueprint",
        description="Full map after copy decode (all top-level BP.Entries).",
        after_state_json={"decode": frame_summary},
        cell_overlay_json={"cells": full_map},
        metrics_json=norm_metrics,
        is_decision_point=True,
        full_map=list(full_map),
        diff={"added": [], "removed": [], "changed": []},
        summary=frame_summary,
    )

    return recorder.record_many([ev_decode])


def persist_decoded_cell_snapshot(
    project_id: int,
    map_input_id: int,
    snapshot: DecodedBlueprintSnapshotDTO,
) -> int:
    """Persist one :class:`AsteroidCellSnapshot` compatible with generic JSON fields.

    ``AsteroidCellSnapshot`` stores overlay rows under ``overlay_json``; grid metadata under
    ``cell_grid_json``. This is optional UI/cache material — never solver algorithm input.
    """

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)
    if int(inp.project_id) != int(project_id):
        msg = "map_input.project_id does not match project_id"
        raise ValueError(msg)

    overlay: dict[str, Any] = {
        "schema": "asteroid_lab_decoded_blueprint_v1",
        "cells": [_overlay_cell_dict(c) for c in snapshot.cells],
    }
    grid: dict[str, Any] = {
        "bbox": dict(snapshot.bbox_json),
        "cell_kind_counts": dict(snapshot.cell_kind_counts_json),
        "transport_kind_counts": dict(snapshot.transport_kind_counts_json),
        "entry_count": snapshot.entry_count,
        "blueprint_type": snapshot.blueprint_type,
        "binary_version": snapshot.binary_version,
        "summary": dict(snapshot.summary_json),
        "full_cells": [asdict(c) for c in snapshot.cells],
    }
    row = m.AsteroidCellSnapshot.objects.create(
        map_input=inp,
        layer="decoded_blueprint_top",
        cell_grid_json=grid,
        overlay_json=overlay,
    )
    return int(row.pk)
