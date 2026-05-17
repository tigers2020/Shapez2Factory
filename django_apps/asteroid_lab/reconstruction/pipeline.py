"""Topology fill after cleanup (pure; not solver input)."""

from __future__ import annotations

from collections.abc import Set
from typing import TYPE_CHECKING

from django_apps.asteroid_lab.reconstruction.fill import (
    TOPOLOGY_FILL_PLACEHOLDER_KIND,
    connected_components,
    passes_bbox_interior,
    passes_two_axis_evidence_guard,
    synthetic_field_cell,
)
from django_apps.asteroid_lab.reconstruction.flood_fill import external_reachable
from django_apps.asteroid_lab.reconstruction.grid import Coord, iter_bbox_cells
from django_apps.asteroid_lab.reconstruction.island import stamp_islands_uniform
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.shell import infer_shell_barrier_coords
from django_apps.asteroid_lab.reconstruction.trace import (
    ReconstructionTraceCollector,
    ReconstructionTraceEvent,
)
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.server_coords import server_xy_for_raw_xy
from django_apps.asteroid_lab.snapshots.transport_components import sort_key_xy_layer

if TYPE_CHECKING:
    from django_apps.asteroid_lab.cleanup.result import CleanupResult


def _sorted_interior_components(interior: set[Coord]) -> list[set[Coord]]:
    comps = connected_components(interior)
    return sorted(
        comps,
        key=lambda comp: (
            min(y for _x, y in comp),
            min(x for x, _y in comp),
            len(comp),
        ),
    )


def reconstruct_after_cleanup(
    *,
    cleaned_cells: tuple[DecodedCellDTO, ...],
    original_cells: tuple[DecodedCellDTO, ...],
    removed_building_cells: tuple[DecodedCellDTO, ...] = (),
    wall_coords: Set[Coord] | frozenset[Coord],
    bbox_bounds: tuple[int, int, int, int] | None,
    server_xy_params: tuple[int, int] | None,
    trace_collector: ReconstructionTraceCollector | None = None,
) -> ReconstructionResult:
    """Flood-fill and fill enclosed holes using precomputed walls and bbox (no snapshot DTO).

    ``wall_coords`` (cleanup evidence + removed miner/extension anchors) define fill guards.
    ``barrier_xy = wall_coords ∪ inferred_shell`` blocks external flood-fill only; inferred
    segments must not be passed to ``passes_two_axis_evidence_guard`` (overfill risk).

    Topology holes are filled with a placeholder ``cell_kind``; final ``asteroid_*_field`` on
    every non-transport island comes from :func:`stamp_islands_uniform`.
    """

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

    if trace_collector is not None:
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="wall_projection",
                coords=frozenset(walls_xy),
                summary_json={
                    "event_key": "step4_00_wall_projection",
                    "trace_event_type": "wall_projection",
                    "wall_cell_count": len(walls_xy),
                },
            )
        )

    if bbox_bounds is None:
        summary["skip_reason"] = "no_topology_barriers"
        if trace_collector is not None:
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="reconstruction_skip",
                    coords=frozenset(),
                    summary_json={
                        "event_key": "step4_09_reconstruction_skip",
                        "trace_event_type": "reconstruction_skip",
                        "skip_reason": "no_topology_barriers",
                    },
                )
            )
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="reconstruction_final",
                    coords=frozenset(),
                    summary_json={
                        "event_key": "step4_09_reconstruction_final",
                        "trace_event_type": "reconstruction_final",
                    },
                )
            )
        stamped = stamp_islands_uniform(
            tuple(sorted(stripped, key=sort_key_xy_layer)),
            original_cells=original_cells,
            removed_building_cells=removed_building_cells,
        )
        return ReconstructionResult(
            cells=stamped,
            summary_json=dict(summary),
            outer_rim_coords=(),
        )

    w0, w1, h0, h1 = bbox_bounds
    inferred_frozen = infer_shell_barrier_coords(
        wall_coords, bbox_bounds, trace_collector=trace_collector
    )
    inferred_xy: set[Coord] = set(inferred_frozen)
    barrier_xy: set[Coord] = walls_xy | inferred_xy

    if trace_collector is not None:
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="barrier_build",
                coords=frozenset(barrier_xy),
                summary_json={
                    "event_key": "step4_03_barrier_build",
                    "trace_event_type": "barrier_build",
                    "wall_cell_count": len(walls_xy),
                    "inferred_shell_cell_count": len(inferred_frozen - walls_xy),
                    "barrier_cell_count": len(barrier_xy),
                },
            )
        )

    walkable: set[Coord] = set()
    for xy in iter_bbox_cells(w0, w1, h0, h1):
        if xy not in barrier_xy:
            walkable.add(xy)

    external = external_reachable(
        walkable,
        w0=w0,
        w1=w1,
        h0=h0,
        h1=h1,
        trace_collector=trace_collector,
    )
    interior = walkable - external

    if trace_collector is not None:
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="interior_candidates",
                coords=frozenset(interior),
                summary_json={
                    "event_key": "step4_05_interior_candidates",
                    "trace_event_type": "interior_candidates",
                    "interior_candidate_count": len(interior),
                },
            )
        )

    interior_comps = _sorted_interior_components(interior)
    skipped_bbox = 0
    skipped_guard = 0
    filled_components = 0
    filled: list[DecodedCellDTO] = []

    for comp_index, comp in enumerate(interior_comps):
        if trace_collector is not None:
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="component_detected",
                    coords=frozenset(comp),
                    summary_json={
                        "event_key": f"step4_06_component_{comp_index:03d}_detected",
                        "trace_event_type": "component_detected",
                        "component_index": comp_index,
                        "component_size": len(comp),
                    },
                )
            )

        if not passes_bbox_interior(comp, w0, w1, h0, h1):
            skipped_bbox += 1
            if trace_collector is not None:
                trace_collector.append(
                    ReconstructionTraceEvent(
                        phase="reconstruction",
                        trace_event_type="component_guard",
                        coords=frozenset(comp),
                        summary_json={
                            "event_key": f"step4_06_component_{comp_index:03d}_guard",
                            "trace_event_type": "component_guard",
                            "component_index": comp_index,
                            "guard_outcome": "rejected_bbox",
                        },
                    )
                )
            continue
        if not passes_two_axis_evidence_guard(comp, walls_xy):
            skipped_guard += 1
            if trace_collector is not None:
                trace_collector.append(
                    ReconstructionTraceEvent(
                        phase="reconstruction",
                        trace_event_type="component_guard",
                        coords=frozenset(comp),
                        summary_json={
                            "event_key": f"step4_06_component_{comp_index:03d}_guard",
                            "trace_event_type": "component_guard",
                            "component_index": comp_index,
                            "guard_outcome": "rejected_evidence",
                        },
                    )
                )
            continue

        if trace_collector is not None:
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="component_guard",
                    coords=frozenset(comp),
                    summary_json={
                        "event_key": f"step4_06_component_{comp_index:03d}_guard",
                        "trace_event_type": "component_guard",
                        "component_index": comp_index,
                        "guard_outcome": "accepted",
                    },
                )
            )

        filled_components += 1
        kind = TOPOLOGY_FILL_PLACEHOLDER_KIND
        fill_layer: int | None = stripped[0].layer if stripped else None
        fill_xy: list[Coord] = []
        for x, y in sorted(comp):
            if (x, y) in occupied_xy:
                continue
            fill_xy.append((x, y))
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

        if trace_collector is not None and fill_xy:
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="fill_commit",
                    coords=frozenset(fill_xy),
                    summary_json={
                        "event_key": f"step4_06_component_{comp_index:03d}_fill",
                        "trace_event_type": "fill_commit",
                        "component_index": comp_index,
                        "cell_kind": kind,
                        "filled_cell_count": len(fill_xy),
                        "note": "placeholder_kind_before_island_stamp",
                    },
                )
            )

    summary["inferred_shell_cell_count"] = len(inferred_frozen - walls_xy)
    summary["barrier_cell_count"] = len(barrier_xy)
    summary["external_reachable_count"] = len(external)
    summary["interior_candidate_count"] = len(interior)
    summary["interior_component_count"] = len(interior_comps)
    summary["filled_component_count"] = filled_components
    summary["skipped_component_count"] = skipped_bbox + skipped_guard
    summary["filled_hole_cell_count"] = len(filled)

    merged: dict[tuple[int, int, int | None], DecodedCellDTO] = dict(stripped_by_key)
    for cell in filled:
        key = (cell.x, cell.y, cell.layer)
        merged[key] = cell

    merged_tuple = tuple(sorted(merged.values(), key=sort_key_xy_layer))
    out_cells = stamp_islands_uniform(
        merged_tuple,
        original_cells=original_cells,
        removed_building_cells=removed_building_cells,
    )

    if trace_collector is not None:
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="reconstruction_final",
                coords=frozenset(),
                summary_json={
                    "event_key": "step4_09_reconstruction_final",
                    "trace_event_type": "reconstruction_final",
                },
            )
        )

    return ReconstructionResult(
        cells=out_cells,
        summary_json=dict(summary),
        outer_rim_coords=(),
    )


def run_topology_reconstruction(
    cleanup: CleanupResult,
    trace_collector: ReconstructionTraceCollector | None = None,
) -> ReconstructionResult:
    """Fill enclosed holes from ``CleanupResult`` walls and bbox."""

    return reconstruct_after_cleanup(
        cleaned_cells=cleanup.cleaned_cells,
        original_cells=cleanup.original_cells,
        removed_building_cells=cleanup.removed_building_cells,
        wall_coords=cleanup.wall_coords,
        bbox_bounds=cleanup.bbox_bounds,
        server_xy_params=cleanup.server_xy_params,
        trace_collector=trace_collector,
    )


def reconstruct_snapshot(snapshot: DecodedBlueprintSnapshotDTO) -> ReconstructionResult:
    """Decode snapshot → cleanup → topology reconstruction (convenience wrapper)."""

    from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot

    c = deconstruct_snapshot(snapshot)
    return reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        server_xy_params=c.server_xy_params,
    )
