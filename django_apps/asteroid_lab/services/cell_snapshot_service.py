"""Decoded blueprint snapshot: ORM read, replay frames, optional ``AsteroidCellSnapshot`` row."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.observability.boundary_jsonl import DJANGO_BOUNDARY_SINK
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_DECODE_NORMALIZED,
    EVENT_TYPE_DECODE_RAW_LOADED,
)
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    build_cleanup_and_reconstruction_rows,
    decode_snapshot_summary,
    diff_maps,
    snapshot_summary_from_rows,
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
from django_apps.asteroid_lab.snapshots.equipment_bundles import build_equipment_bundles


def build_decoded_blueprint_snapshot_from_input(
    map_input_id: int,
    *,
    boundary_run_id: str | None = None,
) -> DecodedBlueprintSnapshotDTO:
    """Load ``AsteroidMapInput.decoded_json`` and build a pure snapshot DTO."""

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)
    raw = inp.decoded_json
    decoded: dict[str, object] = dict(raw) if isinstance(raw, dict) else {}
    rid = boundary_run_id if boundary_run_id is not None else f"map_input:{int(map_input_id)}"
    return build_decoded_blueprint_snapshot(
        decoded,
        project_id=int(inp.project_id),
        map_input_id=int(inp.id),
        boundary_run_id=rid,
        boundary_sink=DJANGO_BOUNDARY_SINK,
    )


def _overlay_cell_dict(c: DecodedCellDTO) -> dict[str, object]:
    row: dict[str, object] = {
        "x": c.x,
        "y": c.y,
        "layer": c.layer,
        "rotation": c.rotation,
        "cell_kind": c.cell_kind,
        "transport_kind": c.transport_kind,
        "tile_type": c.tile_type,
    }
    return row


def record_decoded_snapshot_frames(
    track_id: int,
    snapshot: DecodedBlueprintSnapshotDTO,
) -> list[SnapshotFrameDTO]:
    """Append decode replay frames: raw full map, then transport-stripped map + removal diff."""

    recorder = ReplayRecorder(int(track_id))
    bv = snapshot.binary_version
    row_decode, row_transport, *_ = build_cleanup_and_reconstruction_rows(snapshot)
    full_map_raw = [dict(r) for r in row_decode]
    full_map_norm = [dict(r) for r in row_transport]
    transport_diff = diff_maps(row_decode, row_transport)
    raw_decode = decode_snapshot_summary(snapshot)
    summary_raw = snapshot_summary_from_rows(row_decode)
    summary_norm = snapshot_summary_from_rows(row_transport)
    raw_metrics: dict[str, object] = {
        "binary_version": bv,
        "blueprint_type": snapshot.blueprint_type,
        "entry_count": snapshot.entry_count,
        "cell_kind_counts": dict(summary_raw["cell_kind_counts"]),
        "transport_kind_counts": dict(
            Counter(str(r.get("transport_kind") or "none") for r in row_decode)
        ),
        "bbox": dict(snapshot.bbox_json),
    }
    norm_metrics: dict[str, object] = {
        "binary_version": bv,
        "blueprint_type": snapshot.blueprint_type,
        "entry_count": snapshot.entry_count,
        "cell_kind_counts": dict(summary_norm["cell_kind_counts"]),
        "transport_kind_counts": dict(
            Counter(str(r.get("transport_kind") or "none") for r in row_transport)
        ),
        "bbox": dict(snapshot.bbox_json),
    }

    ev_raw = SnapshotEventDTO(
        event_key="step0_decode_raw",
        phase="decode",
        phase_step="raw",
        event_type=EVENT_TYPE_DECODE_RAW_LOADED,
        title="Decoded blueprint (raw)",
        description="Copy decode: full blueprint as decoded from copy (transport included).",
        after_state_json={"decode": raw_decode},
        cell_overlay_json={
            "cells": full_map_raw,
            "equipment_bundles": build_equipment_bundles(full_map_raw),
        },
        metrics_json=raw_metrics,
        is_decision_point=True,
        full_map=full_map_raw,
        diff={"added": [], "removed": [], "changed": []},
        summary=summary_raw,
    )

    ev_norm = SnapshotEventDTO(
        event_key="step0_decode",
        phase="decode",
        phase_step="normalized",
        event_type=EVENT_TYPE_DECODE_NORMALIZED,
        title="Decoded blueprint",
        description="Copy decode with existing transport stripped for solver-facing map.",
        after_state_json={"decode": raw_decode},
        cell_overlay_json={
            "cells": full_map_norm,
            "equipment_bundles": build_equipment_bundles(full_map_norm),
        },
        metrics_json=norm_metrics,
        is_decision_point=True,
        full_map=full_map_norm,
        diff=transport_diff,
        summary=summary_norm,
    )

    return recorder.record_many([ev_raw, ev_norm])


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

    overlay: dict[str, object] = {
        "schema": "asteroid_lab_decoded_blueprint_v1",
        "cells": [_overlay_cell_dict(c) for c in snapshot.cells],
    }
    grid: dict[str, object] = {
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
