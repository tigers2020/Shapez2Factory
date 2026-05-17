"""Strip buildings and compute topology wall coordinates (pre-reconstruction)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.cleanup.result import BBoxBounds, CleanupResult
from django_apps.asteroid_lab.reconstruction.evidence import (
    MINER_EXTENSION_CELL_KINDS,
    is_asteroid_evidence,
    is_strippable_building,
)
from django_apps.asteroid_lab.reconstruction.grid import Coord, padded_bbox_bounds
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.server_coords import (
    map_bbox_dense_and_y,
    server_xy_for_raw_xy,
)
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile


def _attach_missing_server_coords(
    cells: tuple[DecodedCellDTO, ...],
    *,
    server_xy_params: tuple[int, int] | None,
) -> tuple[DecodedCellDTO, ...]:
    if server_xy_params is None:
        return cells
    max_dense_x, min_raw_y = server_xy_params
    out = []
    for cell in cells:
        if cell.server_x is not None and cell.server_y is not None:
            out.append(cell)
            continue
        if cell.x == 0:
            # import 경계에서만 raw X==0을 명시적 server x==0으로 정규화한다.
            out.append(replace(cell, server_x=0, server_y=cell.y - min_raw_y))
            continue
        pair = server_xy_for_raw_xy(
            cell.x,
            cell.y,
            max_dense_x=max_dense_x,
            min_raw_y=min_raw_y,
        )
        if pair is None:
            out.append(cell)
        else:
            out.append(replace(cell, server_x=pair[0], server_y=pair[1]))
    return tuple(out)


def deconstruct_snapshot(snapshot: DecodedBlueprintSnapshotDTO) -> CleanupResult:
    """Remove strippable buildings and compute ``wall_coords`` for reconstruction."""

    raw_cells = snapshot.cells
    params = map_bbox_dense_and_y([{"X": c.x, "Y": c.y} for c in raw_cells])
    server_xy_params: tuple[int, int] | None = None
    if params is not None:
        server_xy_params = (int(params[0]), int(params[1]))

    cells = _attach_missing_server_coords(raw_cells, server_xy_params=server_xy_params)
    removed = tuple(c for c in cells if is_strippable_building(c))
    ignored_transport = tuple(c for c in removed if is_transport_tile(c))
    cleaned = tuple(c for c in cells if not is_strippable_building(c))

    walls: set[Coord] = set()
    for c in cells:
        if is_asteroid_evidence(c):
            walls.add((c.x, c.y))
    for c in removed:
        if c.cell_kind in MINER_EXTENSION_CELL_KINDS:
            walls.add((c.x, c.y))

    wall_frozen = frozenset(walls)
    bbox_bounds: BBoxBounds | None
    bbox_bounds = padded_bbox_bounds(set(wall_frozen), pad=1)
    summary: dict[str, object] = {
        "cleanup_removed_building_count": len(removed),
        "cleanup_ignored_transport_count": len(ignored_transport),
        "cleanup_wall_coord_count": len(wall_frozen),
    }

    return CleanupResult(
        cleaned_cells=cleaned,
        removed_building_cells=removed,
        ignored_transport_cells=ignored_transport,
        wall_coords=wall_frozen,
        bbox_bounds=bbox_bounds,
        server_xy_params=server_xy_params,
        original_cells=tuple(cells),
        summary_json=dict(summary),
    )
