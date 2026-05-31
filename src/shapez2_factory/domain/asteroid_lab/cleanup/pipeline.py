"""Strip buildings and compute topology wall coordinates (pre-reconstruction)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.cleanup.result import BBoxBounds, CleanupResult
from shapez2_factory.domain.asteroid_lab.observability.boundary_sink import (
    NO_OP_BOUNDARY_SINK,
    BoundaryTraceSink,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.evidence import (
    MINER_EXTENSION_CELL_KINDS,
    is_asteroid_evidence,
    is_strippable_building,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.grid import Coord, padded_bbox_bounds
from shapez2_factory.domain.asteroid_lab.service_dtos import DecodedBlueprintSnapshotDTO
from shapez2_factory.domain.asteroid_lab.transport_components import is_transport_tile


def deconstruct_snapshot(
    snapshot: DecodedBlueprintSnapshotDTO,
    *,
    boundary_run_id: str | None = None,
    boundary_sink: BoundaryTraceSink | None = None,
) -> CleanupResult:
    """Remove strippable buildings and compute ``wall_coords`` for reconstruction."""

    cells = snapshot.cells
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

    if boundary_run_id:
        removed_payload = []
        for c in removed:
            row = {
                "raw_x": c.x,
                "raw_y": c.y,
                "layer": c.layer,
                "cell_kind": c.cell_kind,
            }
            removed_payload.append(row)
        (boundary_sink or NO_OP_BOUNDARY_SINK).emit(
            run_id=boundary_run_id,
            stage="cleanup",
            boundary="cleanup.cell_removed",
            data={
                "map_input_id": snapshot.map_input_id,
                "project_id": snapshot.project_id,
                "removed_cell_count": len(removed_payload),
                "removed_cells": removed_payload,
                "cleaned_cell_count": len(cleaned),
                "summary": dict(summary),
            },
        )

    return CleanupResult(
        cleaned_cells=cleaned,
        removed_building_cells=removed,
        ignored_transport_cells=ignored_transport,
        wall_coords=wall_frozen,
        bbox_bounds=bbox_bounds,
        original_cells=tuple(cells),
        summary_json=dict(summary),
    )


__all__ = ["deconstruct_snapshot"]
