"""Attach terrain rim highlight wire to Lab replay timeline frames (output-only)."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_decoded_cells,
)
from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.reconstruction.rim_highlight import (
    build_terrain_rim_highlight_from_renderable_cells,
    terrain_rim_highlight_to_metrics_dict,
)
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

LAB_PHASE_RECONSTRUCTION = "reconstruction"
METRICS_KEY = "terrain_rim_highlight"


def frame_has_renderable_map(frame: dict[str, Any]) -> bool:
    mv = frame.get("map_view")
    if not isinstance(mv, dict):
        return False
    full_cells = mv.get("full_cells")
    if isinstance(full_cells, list) and len(full_cells) > 0:
        return True
    cell_delta = mv.get("cell_delta")
    if isinstance(cell_delta, list) and len(cell_delta) > 0:
        return True
    overlay = mv.get("overlay_cells")
    return isinstance(overlay, list) and len(overlay) > 0

_COMPLETE_EVENT_TYPES = frozenset(
    {
        ReplayEventType.RECONSTRUCTION_COMPLETED.value,
        EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
    }
)


def _decoded_from_replay_row(row: Mapping[str, Any]) -> DecodedCellDTO:
    layer_raw = row.get("layer")
    layer = int(layer_raw) if layer_raw is not None else None
    return DecodedCellDTO(
        x=int(row["x"]),
        y=int(row["y"]),
        layer=layer,
        rotation=int(row.get("rotation") or 0),
        tile_type=str(row.get("tile_type") or ""),
        cell_kind=str(row.get("cell_kind") or row.get("kind") or ""),
        transport_kind=str(row.get("transport_kind") or row.get("transport") or "none"),
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def _full_cell_rows_from_frame(frame: Mapping[str, Any]) -> list[dict[str, Any]]:
    map_view = frame.get("map_view")
    if not isinstance(map_view, dict):
        return []
    full_cells = map_view.get("full_cells")
    if not isinstance(full_cells, list):
        return []
    return [row for row in full_cells if isinstance(row, dict)]


def _topology_from_renderable_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> tuple[frozenset[Coord], frozenset[Coord]]:
    cells = tuple(_decoded_from_replay_row(row) for row in rows)
    field_cells: set[Coord] = set()
    for cell in cells:
        if cell.cell_kind in ASTEROID_FIELD_KINDS:
            field_cells.add((cell.x, cell.y))
    field_frozen = frozenset(field_cells)
    topo = acceptance_topology_from_decoded_cells(
        cells,
        field_cells=field_frozen,
        coord_frame=coord_frame,
    )
    return field_frozen, topo.external_void_cells


def _highlight_wire_from_frame_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> dict[str, object]:
    field_cells, external_void = _topology_from_renderable_rows(rows, coord_frame=coord_frame)
    dto = build_terrain_rim_highlight_from_renderable_cells(
        field_cells=field_cells,
        external_void_cells=external_void,
        coord_frame=coord_frame,
    )
    return terrain_rim_highlight_to_metrics_dict(dto)


def _is_complete_frame(frame: Mapping[str, Any]) -> bool:
    event_type = str(frame.get("event_type") or "")
    if event_type in _COMPLETE_EVENT_TYPES:
        return True
    inspector = frame.get("inspector")
    if isinstance(inspector, dict):
        lab_event = str(inspector.get("lab_event_type") or "")
        if lab_event in _COMPLETE_EVENT_TYPES:
            return True
    return False


def enrich_lab_timeline_frames_with_terrain_rim(
    frames: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, object] | None]:
    """Return enriched frames and optional frozen complete-map rim wire."""

    frozen_wire: dict[str, object] | None = None
    out: list[dict[str, Any]] = []
    for frame in frames:
        fr_copy = copy.deepcopy(frame)
        metrics = dict(fr_copy.get("metrics") or {})
        if METRICS_KEY in metrics:
            del metrics[METRICS_KEY]
        if not frame_has_renderable_map(fr_copy):
            fr_copy["metrics"] = metrics
            out.append(fr_copy)
            continue
        inspector = fr_copy.get("inspector")
        lab_phase = ""
        if isinstance(inspector, dict):
            lab_phase = str(inspector.get("lab_phase") or "")
        if frozen_wire is not None:
            pass
        elif lab_phase == LAB_PHASE_RECONSTRUCTION:
            rows = _full_cell_rows_from_frame(fr_copy)
            wire = _highlight_wire_from_frame_rows(rows)
            metrics[METRICS_KEY] = wire
            if _is_complete_frame(fr_copy):
                frozen_wire = wire
        fr_copy["metrics"] = metrics
        out.append(fr_copy)
    return out, frozen_wire


__all__ = [
    "LAB_PHASE_RECONSTRUCTION",
    "METRICS_KEY",
    "enrich_lab_timeline_frames_with_terrain_rim",
]
