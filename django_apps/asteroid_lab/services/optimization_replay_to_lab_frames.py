"""Map optimization replay frames onto Lab ``ReplayFrameAppendDTO`` rows (output-only).

**App-boundary exception:** lives under ``asteroid_lab`` but imports
``shapez_asteroid.optimization`` DTOs only to adapt recorder output into Lab
append payloads (one-way). Documented as *boundary exception: output-only
adapter* in ``asteroid_lab_00_overview.md``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict
from typing import Any

from django_apps.asteroid_lab.replay.snapshot_map_replay import cell_key_xy_layer, diff_maps
from django_apps.asteroid_lab.services.dto import ReplayFrameAppendDTO, SnapshotEventDTO
from django_apps.asteroid_lab.snapshots.equipment_bundles import build_equipment_bundles
from django_apps.shapez_asteroid.optimization.dto import (
    IncrementalCommitResult,
    OptimizationReplayFrame,
)
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.shapez_asteroid.optimization.optimization_replay import json_safe_replay_value

COMMIT_CLASS_OPTIMIZATION_EVENT_TYPES: frozenset[str] = frozenset(
    {OptimizationReplayEventType.ROUTE_COMMITTED.value}
)


def _slug_from_event_type(event_type: OptimizationReplayEventType) -> str:
    s = str(event_type.value).replace(".", "_")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", s).strip("_").lower()


def _metrics_json_safe(metrics: Mapping[str, object]) -> dict[str, Any]:
    raw = json_safe_replay_value(dict(metrics))
    return dict(raw) if isinstance(raw, dict) else {"value": raw}


def _overlay_rows_from_cells(cells: tuple[object, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for c in cells:
        row = json_safe_replay_value(c)
        if isinstance(row, dict) and "x" in row and "y" in row:
            r = dict(row)
            r.setdefault("layer", 0)
            r.setdefault("rotation", 0)
            r.setdefault("cell_kind", "optimization_overlay")
            r.setdefault("transport_kind", "none")
            r.setdefault("tile_type", "")
            rows.append(r)
    return rows


def _cell_overlay_json(visible: tuple[object, ...], overlay: tuple[object, ...]) -> dict[str, Any]:
    rows = _overlay_rows_from_cells(visible) + _overlay_rows_from_cells(overlay)
    return {"cells": rows, "equipment_bundles": build_equipment_bundles(rows)}


def _index_rows(rows: list[dict[str, Any]]) -> dict[tuple[int, int, int | None], dict[str, Any]]:
    return {cell_key_xy_layer(r): dict(r) for r in rows}


def _transport_tile_type(kind_value: str) -> str:
    if kind_value == "fluid_pipe":
        return "SpacePipe_Straight"
    return "SpaceBelt_Straight"


def _apply_reservation_path_to_rows(
    rows: list[dict[str, Any]],
    *,
    path: tuple[Any, ...],
    transport_kind_value: str,
) -> None:
    by_key = _index_rows(rows)
    for step in path:
        if hasattr(step, "x") and hasattr(step, "y"):
            x, y = int(step.x), int(step.y)
            ly_raw = getattr(step, "layer", None)
            ly: int | None = None if ly_raw is None else int(ly_raw)
        else:
            coord = json_safe_replay_value(step)
            if not isinstance(coord, dict) or "x" not in coord or "y" not in coord:
                continue
            x, y = int(coord["x"]), int(coord["y"])
            layer = coord.get("layer")
            ly = None if layer is None else int(layer)
        key = (x, y, ly)
        row = {
            "x": x,
            "y": y,
            "layer": ly,
            "rotation": 0,
            "cell_kind": "transport",
            "transport_kind": transport_kind_value,
            "tile_type": _transport_tile_type(transport_kind_value),
        }
        by_key[key] = row
    rows[:] = sorted(by_key.values(), key=lambda r: (int(r["y"]), int(r["x"]), r.get("layer") or 0))


def optimization_replay_frames_to_lab_append_dtos(
    frames: Sequence[OptimizationReplayFrame],
    *,
    baseline_full_map: list[dict[str, Any]],
    commit_result: IncrementalCommitResult | None = None,
) -> list[ReplayFrameAppendDTO]:
    """Convert optimization recorder output to Lab replay append payloads.

    v0: only ``route.committed`` may advance the physical ``full_map`` (see
    ``COMMIT_CLASS_OPTIMIZATION_EVENT_TYPES``). Other events keep the current
    materialized map and attach overlay/metrics only.
    """

    working: list[dict[str, Any]] = [dict(r) for r in baseline_full_map]
    reservations_by_id: dict[str, Any] = {}
    if commit_result is not None:
        for rv in commit_result.route_reservations:
            reservations_by_id[str(rv.reservation_id)] = rv

    out: list[ReplayFrameAppendDTO] = []
    for local_i, frame in enumerate(frames):
        before_map = deepcopy(working)
        et = frame.event_type.value
        if et in COMMIT_CLASS_OPTIMIZATION_EVENT_TYPES and commit_result is not None:
            rid = frame.metrics.get("route_reservation_id")
            res = reservations_by_id.get(str(rid)) if rid is not None else None
            if res is not None and res.path:
                tk = (
                    res.transport_kind.value
                    if hasattr(res.transport_kind, "value")
                    else str(res.transport_kind)
                )
                _apply_reservation_path_to_rows(working, path=res.path, transport_kind_value=tk)

        full_map_snapshot = deepcopy(working)
        overlay = _cell_overlay_json(frame.visible_cells, frame.overlay_cells)
        metrics = _metrics_json_safe(frame.metrics)
        diff = diff_maps(before_map, full_map_snapshot)

        event_key = f"optimization_{local_i:02d}_{_slug_from_event_type(frame.event_type)}"
        snap = SnapshotEventDTO(
            event_key=event_key,
            phase="optimization",
            phase_step="",
            event_type=et,
            title=frame.title,
            description=frame.description,
            before_state_json={},
            after_state_json={},
            delta_json={},
            cell_overlay_json=overlay,
            focus_cells_json=[],
            candidate_ref="",
            bundle_ref="",
            route_ref=str(frame.metrics.get("route_reservation_id") or ""),
            is_decision_point=True,
            is_reversible=True,
            is_placeholder=False,
            severity="info",
            metrics_json=metrics,
            full_map=full_map_snapshot,
            diff=dict(diff) if isinstance(diff, dict) else {},
            summary=dict(metrics),
        )
        payload = asdict(snap)
        out.append(
            ReplayFrameAppendDTO(
                frame_key=event_key,
                phase="optimization",
                title=frame.title,
                description=frame.description,
                frame_payload=payload,
                cell_overlay_json=dict(overlay),
                metric_snapshot_json=metrics,
                is_placeholder=False,
                is_keyframe=True,
                frame_index=None,
            )
        )
    return out
