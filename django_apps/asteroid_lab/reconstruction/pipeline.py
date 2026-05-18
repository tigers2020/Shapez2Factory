"""Topology fill after cleanup (pure; not solver input)."""

from __future__ import annotations

from collections.abc import Set
from typing import TYPE_CHECKING

from django_apps.asteroid_lab.observability.boundary_jsonl import (
    emit_boundary_jsonl,
    summarize_cell_kind_transitions,
)
from django_apps.asteroid_lab.reconstruction.fill import (
    TOPOLOGY_FILL_PLACEHOLDER_KIND,
    connected_components,
    passes_bbox_interior,
    synthetic_field_cell,
)
from django_apps.asteroid_lab.reconstruction.flood_fill import external_reachable
from django_apps.asteroid_lab.reconstruction.grid import Coord, iter_bbox_cells
from django_apps.asteroid_lab.reconstruction.island import stamp_islands_uniform
from django_apps.asteroid_lab.reconstruction.perimeter_closing import chebyshev_close_barrier
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


def _emit_reconstruction_stamp_boundary(
    boundary_run_id: str | None,
    before_cells: tuple[DecodedCellDTO, ...],
    after_cells: tuple[DecodedCellDTO, ...],
    *,
    map_input_id: int | None,
    project_id: int | None,
    summary_json: dict[str, object],
    server_xy_params: tuple[int, int] | None,
) -> None:
    if not boundary_run_id:
        return
    transitions = summarize_cell_kind_transitions(
        before_cells, after_cells, server_xy_params=server_xy_params
    )
    emit_boundary_jsonl(
        run_id=boundary_run_id,
        stage="reconstruction",
        boundary="reconstruction.island_stamp_cell_kind",
        data={
            "map_input_id": map_input_id,
            "project_id": project_id,
            "transition_count": len(transitions),
            "transitions": transitions,
            "reconstruction_summary": dict(summary_json),
        },
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
    boundary_run_id: str | None = None,
    boundary_map_input_id: int | None = None,
    boundary_project_id: int | None = None,
) -> ReconstructionResult:
    """Flood-fill and fill enclosed holes using precomputed walls and bbox (no snapshot DTO).

    ``wall_coords`` (cleanup evidence + removed miner/extension anchors) feed the flood
    barrier. ``barrier_xy = close(walls ∪ inferred_shell)`` blocks exterior flood; interior
    components fully inside the working bbox are filled (flood-only, no two-axis guard).

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
        before_skip = tuple(sorted(stripped, key=sort_key_xy_layer))
        stamped = stamp_islands_uniform(
            before_skip,
            original_cells=original_cells,
            removed_building_cells=removed_building_cells,
        )
        _emit_reconstruction_stamp_boundary(
            boundary_run_id,
            before_skip,
            stamped,
            map_input_id=boundary_map_input_id,
            project_id=boundary_project_id,
            summary_json=dict(summary),
            server_xy_params=server_xy_params,
        )
        return ReconstructionResult(
            cells=stamped,
            summary_json=dict(summary),
            outer_rim_coords=(),
            server_xy_params=server_xy_params,
        )

    w0, w1, h0, h1 = bbox_bounds
    inferred_frozen = infer_shell_barrier_coords(
        wall_coords, bbox_bounds, trace_collector=trace_collector
    )
    inferred_xy: set[Coord] = set(inferred_frozen)
    barrier_before_close: set[Coord] = walls_xy | inferred_xy
    barrier_xy = chebyshev_close_barrier(
        barrier_before_close,
        bbox_bounds,
        wall_coords=walls_xy,
        trace_collector=trace_collector,
    )
    perimeter_closed_count = len(barrier_xy) - len(barrier_before_close)

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
                    "perimeter_closed_cell_count": perimeter_closed_count,
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
                    min_dense_x=server_xy_params[0],
                    min_raw_y=server_xy_params[1],
                )
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
    summary["perimeter_closed_cell_count"] = perimeter_closed_count
    summary["barrier_cell_count"] = len(barrier_xy)
    summary["external_reachable_count"] = len(external)
    summary["interior_candidate_count"] = len(interior)
    summary["interior_patch_cell_count"] = len(interior)
    summary["interior_component_count"] = len(interior_comps)
    summary["filled_component_count"] = filled_components
    summary["skipped_component_count"] = skipped_bbox
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

    _emit_reconstruction_stamp_boundary(
        boundary_run_id,
        merged_tuple,
        out_cells,
        map_input_id=boundary_map_input_id,
        project_id=boundary_project_id,
        summary_json=dict(summary),
        server_xy_params=server_xy_params,
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
        server_xy_params=server_xy_params,
    )


def run_topology_reconstruction(
    cleanup: CleanupResult,
    trace_collector: ReconstructionTraceCollector | None = None,
    *,
    boundary_run_id: str | None = None,
    boundary_map_input_id: int | None = None,
    boundary_project_id: int | None = None,
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
        boundary_run_id=boundary_run_id,
        boundary_map_input_id=boundary_map_input_id,
        boundary_project_id=boundary_project_id,
    )


def reconstruct_snapshot(
    snapshot: DecodedBlueprintSnapshotDTO,
    *,
    boundary_run_id: str | None = None,
) -> ReconstructionResult:
    """Decode snapshot → cleanup → topology reconstruction (convenience wrapper)."""

    from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot

    c = deconstruct_snapshot(snapshot, boundary_run_id=boundary_run_id)
    return reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        server_xy_params=c.server_xy_params,
        boundary_run_id=boundary_run_id,
        boundary_map_input_id=snapshot.map_input_id,
        boundary_project_id=snapshot.project_id,
    )
