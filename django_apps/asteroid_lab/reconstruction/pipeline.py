"""Topology fill after cleanup (pure; not solver input)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Set

from django_apps.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    evidence_field_kind,
)
from django_apps.asteroid_lab.reconstruction.fill import (
    connected_components,
    infer_fill_field_kind,
    passes_bbox_interior,
    passes_two_axis_evidence_guard,
    synthetic_field_cell,
)
from django_apps.asteroid_lab.reconstruction.flood_fill import external_reachable
from django_apps.asteroid_lab.reconstruction.grid import Coord, iter_bbox_cells
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.server_coords import server_xy_for_raw_xy
from django_apps.asteroid_lab.snapshots.transport_components import sort_key_xy_layer


def _field_kind_map_from_cells(cells: Iterable[DecodedCellDTO]) -> dict[Coord, str]:
    m: dict[Coord, str] = {}
    for c in cells:
        k = evidence_field_kind(c)
        if k in ASTEROID_FIELD_KINDS:
            m[(c.x, c.y)] = k
    return m


def _global_field_counter_from_cells(cells: Iterable[DecodedCellDTO]) -> Counter[str]:
    ctr: Counter[str] = Counter()
    for c in cells:
        k = evidence_field_kind(c)
        if k in ASTEROID_FIELD_KINDS:
            ctr[k] += 1
    return ctr


def reconstruct_after_cleanup(
    *,
    cleaned_cells: tuple[DecodedCellDTO, ...],
    wall_coords: Set[Coord] | frozenset[Coord],
    bbox_bounds: tuple[int, int, int, int] | None,
    server_xy_params: tuple[int, int] | None,
) -> ReconstructionResult:
    """Flood-fill and fill enclosed holes using precomputed walls and bbox (no snapshot DTO)."""

    walls_xy: set[Coord] = set(wall_coords)
    stripped = list(cleaned_cells)
    stripped_by_key: dict[tuple[int, int, int | None], DecodedCellDTO] = {
        (c.x, c.y, c.layer): c for c in stripped
    }
    occupied_xy: set[Coord] = {(c.x, c.y) for c in stripped}

    summary: dict[str, object] = {
        "outer_rim_pending": True,
        "wall_cell_count": len(walls_xy),
        "filled_hole_cell_count": 0,
    }

    if bbox_bounds is None:
        summary["skip_reason"] = "no_topology_barriers"
        return ReconstructionResult(
            cells=tuple(sorted(stripped, key=sort_key_xy_layer)),
            summary_json=dict(summary),
            outer_rim_coords=(),
        )

    w0, w1, h0, h1 = bbox_bounds
    walkable: set[Coord] = set()
    for xy in iter_bbox_cells(w0, w1, h0, h1):
        if xy not in walls_xy:
            walkable.add(xy)

    external = external_reachable(walkable, w0=w0, w1=w1, h0=h0, h1=h1)
    interior = walkable - external

    field_by_xy = _field_kind_map_from_cells(cleaned_cells)
    global_ctr = _global_field_counter_from_cells(cleaned_cells)

    filled: list[DecodedCellDTO] = []
    for comp in connected_components(interior):
        if not passes_bbox_interior(comp, w0, w1, h0, h1):
            continue
        if not passes_two_axis_evidence_guard(comp, walls_xy):
            continue
        kind = infer_fill_field_kind(comp, field_by_xy, global_ctr)
        fill_layer: int | None = stripped[0].layer if stripped else None
        for x, y in sorted(comp):
            if (x, y) in occupied_xy:
                continue
            sx: int | None = None
            sy: int | None = None
            if server_xy_params is not None:
                pair = server_xy_for_raw_xy(
                    x,
                    y,
                    max_dense_x=server_xy_params[0],
                    min_raw_y=server_xy_params[1],
                )
                if pair is not None:
                    sx, sy = pair
            filled.append(synthetic_field_cell(x, y, fill_layer, kind, server_x=sx, server_y=sy))

    summary["filled_hole_cell_count"] = len(filled)

    merged: dict[tuple[int, int, int | None], DecodedCellDTO] = dict(stripped_by_key)
    for cell in filled:
        key = (cell.x, cell.y, cell.layer)
        merged[key] = cell

    out_cells = tuple(sorted(merged.values(), key=sort_key_xy_layer))
    return ReconstructionResult(
        cells=out_cells,
        summary_json=dict(summary),
        outer_rim_coords=(),
    )


def reconstruct_snapshot(snapshot: DecodedBlueprintSnapshotDTO) -> ReconstructionResult:
    """Decode snapshot → cleanup → topology reconstruction (convenience wrapper)."""

    from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot

    c = deconstruct_snapshot(snapshot)
    return reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        server_xy_params=c.server_xy_params,
    )
