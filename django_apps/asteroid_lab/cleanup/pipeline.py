"""Strip buildings and compute topology wall coordinates (pre-reconstruction)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.cleanup.result import BBoxBounds, CleanupResult
from django_apps.asteroid_lab.reconstruction.evidence import (
    MINER_EXTENSION_CELL_KINDS,
    is_asteroid_evidence,
    is_strippable_building,
)
from django_apps.asteroid_lab.reconstruction.grid import Coord, padded_bbox_bounds
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO
from django_apps.asteroid_lab.snapshots.server_coords import map_bbox_dense_and_y
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile


def _trace_event(trace_logger: Any | None, **payload: Any) -> None:
    if trace_logger is None:
        return
    event = getattr(trace_logger, "event", None)
    if callable(event):
        event(**payload)


def deconstruct_snapshot(
    snapshot: DecodedBlueprintSnapshotDTO,
    *,
    trace_logger: Any | None = None,
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
    server_xy_params: tuple[int, int] | None = None
    params = map_bbox_dense_and_y([{"X": c.x, "Y": c.y} for c in cells])
    if params is not None:
        server_xy_params = (int(params[0]), int(params[1]))

    summary: dict[str, object] = {
        "cleanup_removed_building_count": len(removed),
        "cleanup_ignored_transport_count": len(ignored_transport),
        "cleanup_wall_coord_count": len(wall_frozen),
    }
    _trace_event(
        trace_logger,
        stage="cleanup.transport",
        event="cleanup_summary",
        severity="info",
        source={
            "module": "django_apps.asteroid_lab.cleanup.pipeline",
            "function": "deconstruct_snapshot",
        },
        diagnostic={
            **summary,
            "cleaned_cell_count": len(cleaned),
            "original_cell_count": len(cells),
            "server_xy_params": server_xy_params,
        },
    )
    sample_limit = int(getattr(trace_logger, "sample_limit", 128)) if trace_logger else 0
    for c in removed[:sample_limit]:
        after_kind = "none"
        if c.cell_kind in MINER_EXTENSION_CELL_KINDS:
            after_kind = "wall_evidence"
        _trace_event(
            trace_logger,
            stage="cleanup.transport",
            event="cell_removed_or_retyped",
            source={
                "module": "django_apps.asteroid_lab.cleanup.pipeline",
                "function": "deconstruct_snapshot",
            },
            cell={
                "raw_x": c.x,
                "raw_y": c.y,
                "server_x": c.server_x,
                "server_y": c.server_y,
                "cell_kind_before": c.cell_kind,
                "cell_kind_after": after_kind,
                "transport_kind_before": c.transport_kind,
                "transport_kind_after": "none",
                "tile_type": c.tile_type,
            },
            diagnostic={
                "reason": (
                    "transport_removed_during_cleanup"
                    if is_transport_tile(c)
                    else "building_removed_during_cleanup"
                ),
                "source_kind": c.cell_kind,
                "added_to_wall_coords": (c.x, c.y) in wall_frozen,
            },
        )

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
