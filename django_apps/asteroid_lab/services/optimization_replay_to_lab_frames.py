"""Map optimization replay frames onto Lab ``ReplayFrameAppendDTO`` rows (output-only).

**App-boundary exception:** lives under ``asteroid_lab`` but imports
``shapez_asteroid.optimization`` DTOs only to adapt recorder output into Lab
append payloads (one-way). Documented as *boundary exception: output-only
adapter* in ``asteroid_lab_00_overview.md``.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict
from typing import Any

from django_apps.asteroid_lab.replay.snapshot_map_replay import cell_key_xy_layer, diff_maps
from django_apps.asteroid_lab.services.dto import ReplayFrameAppendDTO, SnapshotEventDTO
from django_apps.asteroid_lab.snapshots.equipment_bundles import build_equipment_bundles
from django_apps.asteroid_lab.snapshots.server_coords import (
    map_bbox_dense_and_y_from_lab_rows,
    raw_xy_for_server_xy,
    server_xy_for_raw_xy,
)
from django_apps.shapez_asteroid.optimization.dto import (
    CommittedPlacement,
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


def _overlay_rows_from_cells(
    cells: tuple[object, ...],
    *,
    server_xy_params: tuple[int, int] | None,
    lab_rows: list[dict[str, Any]] | None,
    candidate_id: str | None,
) -> list[dict[str, Any]]:
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
            if server_xy_params is not None:
                sx = int(r["x"])
                sy = int(r["y"])
                max_dx, min_y = int(server_xy_params[0]), int(server_xy_params[1])
                rx, ry = raw_xy_for_server_xy(
                    sx,
                    sy,
                    max_dense_x=max_dx,
                    min_raw_y=min_y,
                    lab_rows=lab_rows,
                )
                r["x"] = rx
                r["y"] = ry
                if os.environ.get("LAB_OVERLAY_DEBUG_SERVER_COORDS", "").strip().lower() in (
                    "1",
                    "true",
                    "yes",
                    "on",
                ):
                    r["debug_server_x"] = sx
                    r["debug_server_y"] = sy
            r.pop("server_x", None)
            r.pop("server_y", None)
            if candidate_id:
                r["optimization_candidate_id"] = candidate_id
            rows.append(r)
    return rows


def _cell_overlay_json(
    visible: tuple[object, ...],
    overlay: tuple[object, ...],
    *,
    server_xy_params: tuple[int, int] | None,
    lab_rows: list[dict[str, Any]] | None,
    frame_metrics: Mapping[str, object],
) -> dict[str, Any]:
    cid = str(frame_metrics.get("candidate_id") or "").strip() or None
    rows = _overlay_rows_from_cells(
        visible,
        server_xy_params=server_xy_params,
        lab_rows=lab_rows,
        candidate_id=cid,
    ) + _overlay_rows_from_cells(
        overlay,
        server_xy_params=server_xy_params,
        lab_rows=lab_rows,
        candidate_id=cid,
    )
    return {"cells": rows, "equipment_bundles": build_equipment_bundles(rows)}


def _index_rows(rows: list[dict[str, Any]]) -> dict[tuple[int, int, int | None], dict[str, Any]]:
    return {cell_key_xy_layer(r): dict(r) for r in rows}


def _transport_tile_type(kind_value: str) -> str:
    if kind_value == "fluid_pipe":
        return "SpacePipe_Straight"
    return "SpaceBelt_Straight"


def _attach_server_axes_to_raw_row(
    row: dict[str, Any],
    *,
    max_dx: int,
    min_y: int,
) -> None:
    sp = server_xy_for_raw_xy(
        int(row["x"]),
        int(row["y"]),
        max_dense_x=max_dx,
        min_raw_y=min_y,
    )
    if sp is not None:
        row["server_x"], row["server_y"] = int(sp[0]), int(sp[1])


def _placement_miner_roles(transport_kind_value: str) -> tuple[tuple[str, str], tuple[str, str]]:
    """``((extractor_cell_kind, extractor_tile), (extension_cell_kind, extension_tile))``."""

    if transport_kind_value == "fluid_pipe":
        return (
            ("fluid_miner", "Layout_FluidMiner"),
            ("fluid_miner_extension", "Layout_FluidMinerExtension"),
        )
    return (
        ("shape_miner", "Layout_ShapeMiner"),
        ("shape_miner_extension", "Layout_ShapeMinerExtension"),
    )


def _apply_committed_placement_for_reservation(
    rows: list[dict[str, Any]],
    *,
    reservation_id: str,
    placements: tuple[CommittedPlacement, ...],
    server_xy_params: tuple[int, int] | None,
    lab_rows: list[dict[str, Any]] | None = None,
) -> None:
    """Materialize extractor/extension **before** route path (belt wins on overlap)."""

    if server_xy_params is None:
        return
    pl = next((p for p in placements if p.route_reservation_id == reservation_id), None)
    if pl is None or pl.extractor is None:
        return
    max_dx, min_y = int(server_xy_params[0]), int(server_xy_params[1])
    lab = lab_rows if lab_rows is not None else rows
    tk = pl.transport_kind.value if hasattr(pl.transport_kind, "value") else str(pl.transport_kind)
    (ex_ck, ex_tile), (ext_ck, ext_tile) = _placement_miner_roles(tk)
    by_key = _index_rows(rows)

    def write_server_cell(sx: int, sy: int, *, cell_kind: str, tile_type: str) -> None:
        rx, ry = raw_xy_for_server_xy(
            sx,
            sy,
            max_dense_x=max_dx,
            min_raw_y=min_y,
            lab_rows=lab,
        )
        stale = [k for k in by_key if k[0] == rx and k[1] == ry]
        for k in stale:
            del by_key[k]
        row: dict[str, Any] = {
            "x": rx,
            "y": ry,
            "layer": 0,
            "rotation": 0,
            "cell_kind": cell_kind,
            "transport_kind": tk,
            "tile_type": tile_type,
        }
        _attach_server_axes_to_raw_row(row, max_dx=max_dx, min_y=min_y)
        by_key[(rx, ry, 0)] = row

    ex = pl.extractor
    write_server_cell(int(ex.x), int(ex.y), cell_kind=ex_ck, tile_type=ex_tile)
    for ext in pl.extensions:
        write_server_cell(int(ext.x), int(ext.y), cell_kind=ext_ck, tile_type=ext_tile)

    rows[:] = sorted(by_key.values(), key=lambda r: (int(r["y"]), int(r["x"]), r.get("layer") or 0))


def _apply_reservation_path_to_rows(
    rows: list[dict[str, Any]],
    *,
    path: tuple[Any, ...],
    transport_kind_value: str,
    server_xy_params: tuple[int, int] | None,
    lab_rows: list[dict[str, Any]] | None = None,
) -> None:
    """Merge transport into ``rows`` at **raw/world** keys.

    ``path`` uses optimization **server** ``Coord`` (see ``shapez_asteroid.optimization.coords``).
    Lab ``full_map`` rows use blueprint raw ``x``/``y``. Strip duplicate ``(x,y,*)`` keys so
    ``layer=None`` vs ``0`` does not leave stale ``asteroid_*`` rows.
    """

    if server_xy_params is None:
        return
    max_dx, min_y = int(server_xy_params[0]), int(server_xy_params[1])
    lab = lab_rows if lab_rows is not None else rows
    by_key = _index_rows(rows)
    for step in path:
        if hasattr(step, "x") and hasattr(step, "y"):
            sx, sy = int(step.x), int(step.y)
        else:
            coord = json_safe_replay_value(step)
            if not isinstance(coord, dict) or "x" not in coord or "y" not in coord:
                continue
            sx, sy = int(coord["x"]), int(coord["y"])
        rx, ry = raw_xy_for_server_xy(
            sx,
            sy,
            max_dense_x=max_dx,
            min_raw_y=min_y,
            lab_rows=lab,
        )
        stale = [k for k in by_key if k[0] == rx and k[1] == ry]
        for k in stale:
            del by_key[k]
        row = {
            "x": rx,
            "y": ry,
            "layer": 0,
            "rotation": 0,
            "cell_kind": "transport",
            "transport_kind": transport_kind_value,
            "tile_type": _transport_tile_type(transport_kind_value),
        }
        _attach_server_axes_to_raw_row(row, max_dx=max_dx, min_y=min_y)
        by_key[(rx, ry, 0)] = row
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
        bbox_proj = map_bbox_dense_and_y_from_lab_rows(working)
        server_xy_proj: tuple[int, int] | None = (
            (int(bbox_proj[0]), int(bbox_proj[1])) if bbox_proj is not None else None
        )
        et = frame.event_type.value
        if et in COMMIT_CLASS_OPTIMIZATION_EVENT_TYPES and commit_result is not None:
            rid = frame.metrics.get("route_reservation_id")
            rid_s = str(rid) if rid is not None else ""
            res = reservations_by_id.get(rid_s) if rid_s else None
            if rid_s:
                _apply_committed_placement_for_reservation(
                    working,
                    reservation_id=rid_s,
                    placements=commit_result.committed_placements,
                    server_xy_params=server_xy_proj,
                    lab_rows=working,
                )
            if res is not None and res.path:
                tk = (
                    res.transport_kind.value
                    if hasattr(res.transport_kind, "value")
                    else str(res.transport_kind)
                )
                _apply_reservation_path_to_rows(
                    working,
                    path=res.path,
                    transport_kind_value=tk,
                    server_xy_params=server_xy_proj,
                    lab_rows=working,
                )

        bbox = map_bbox_dense_and_y_from_lab_rows(working)
        server_xy_params: tuple[int, int] | None = (
            (int(bbox[0]), int(bbox[1])) if bbox is not None else None
        )
        full_map_snapshot = deepcopy(working)
        metrics_src = dict(frame.metrics)
        if server_xy_params is not None:
            metrics_src["server_xy_params"] = [server_xy_params[0], server_xy_params[1]]
        overlay = _cell_overlay_json(
            frame.visible_cells,
            frame.overlay_cells,
            server_xy_params=server_xy_params,
            lab_rows=working,
            frame_metrics=metrics_src,
        )
        metrics = _metrics_json_safe(metrics_src)
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
