"""Miner/extension → asteroid field reconstruction (pure; not solver input)."""

from __future__ import annotations

from collections.abc import Set

from shapez2_factory.domain.asteroid_lab.cleanup.result import CleanupResult
from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.observability.boundary_sink import (
    NO_OP_BOUNDARY_SINK,
    BoundaryTraceSink,
    summarize_cell_kind_transitions,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map_merge import (
    replace_extensions_with_synthetic_fields,
    replace_miners_with_synthetic_fields,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.confidence import (
    apply_confidence_to_result,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    is_asteroid_evidence,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.grid import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.island import stamp_islands_uniform
from shapez2_factory.domain.asteroid_lab.reconstruction.result import ReconstructionResult
from shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract import (
    build_normalized_reconstruction_topology,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.trace import (
    ReconstructionTraceCollector,
    ReconstructionTraceEvent,
)
from shapez2_factory.domain.asteroid_lab.service_dtos import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
)
from shapez2_factory.domain.asteroid_lab.transport_components import (
    sort_key_xy_layer,
)


def _finalize_reconstruction_result(
    cells: tuple[DecodedCellDTO, ...],
    summary: dict[str, object],
    *,
    cleanup: CleanupResult,
    wall_coords: set[Coord],
    shell_raw_coords: frozenset[Coord],
) -> ReconstructionResult:
    base = ReconstructionResult(
        cells=cells,
        summary_json=dict(summary),
        outer_rim_coords=(),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    topo = build_normalized_reconstruction_topology(
        cells,
        shell_raw_coords=shell_raw_coords,
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    return apply_confidence_to_result(
        base,
        wall_coords=wall_coords,
        interior_patch_coords=topo.interior_patch_cells,
        cleanup=cleanup,
    )


def _emit_reconstruction_stamp_boundary(
    boundary_run_id: str | None,
    before_cells: tuple[DecodedCellDTO, ...],
    after_cells: tuple[DecodedCellDTO, ...],
    *,
    map_input_id: int | None,
    project_id: int | None,
    summary_json: dict[str, object],
    boundary_sink: BoundaryTraceSink | None = None,
) -> None:
    if not boundary_run_id:
        return
    transitions = summarize_cell_kind_transitions(before_cells, after_cells)
    (boundary_sink or NO_OP_BOUNDARY_SINK).emit(
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
    trace_collector: ReconstructionTraceCollector | None = None,
    boundary_run_id: str | None = None,
    boundary_map_input_id: int | None = None,
    boundary_project_id: int | None = None,
    boundary_sink: BoundaryTraceSink | None = None,
) -> ReconstructionResult:
    """Convert stripped miners/extensions to ``asteroid_*_field``; stamp island uniformity.

    ``wall_coords`` and ``bbox_bounds`` are retained for API compatibility but are not used
    for flood-fill or barrier morphology.
    """

    del bbox_bounds  # unused — no topology fill

    walls_xy: set[Coord] = set(wall_coords)
    shell_raw_coords: frozenset[Coord] = frozenset(
        (c.x, c.y) for c in original_cells if is_asteroid_evidence(c)
    )
    cleanup_for_finalize = CleanupResult(
        cleaned_cells=cleaned_cells,
        removed_building_cells=removed_building_cells,
        ignored_transport_cells=(),
        wall_coords=frozenset(walls_xy),
        bbox_bounds=None,
        original_cells=original_cells,
    )

    synthetic_from_removed = tuple(
        c
        for c in replace_extensions_with_synthetic_fields(
            replace_miners_with_synthetic_fields(removed_building_cells)
        )
        if c.cell_kind in ASTEROID_FIELD_KINDS
    )

    merged_by_key: dict[tuple[int, int, int | None], DecodedCellDTO] = {
        (c.x, c.y, c.layer): c for c in cleaned_cells
    }
    for cell in synthetic_from_removed:
        merged_by_key[(cell.x, cell.y, cell.layer)] = cell

    merged_tuple = tuple(sorted(merged_by_key.values(), key=sort_key_xy_layer))
    out_cells = stamp_islands_uniform(
        merged_tuple,
        original_cells=original_cells,
        removed_building_cells=removed_building_cells,
    )

    summary: dict[str, object] = {
        "reconstruction_mode": "miner_extension_to_field",
        "synthetic_field_count": len(synthetic_from_removed),
        "filled_hole_cell_count": 0,
    }

    _emit_reconstruction_stamp_boundary(
        boundary_run_id,
        merged_tuple,
        out_cells,
        map_input_id=boundary_map_input_id,
        project_id=boundary_project_id,
        summary_json=dict(summary),
        boundary_sink=boundary_sink,
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
                    "reconstruction_mode": "miner_extension_to_field",
                    "synthetic_field_count": len(synthetic_from_removed),
                },
            )
        )

    return _finalize_reconstruction_result(
        out_cells,
        summary,
        cleanup=cleanup_for_finalize,
        wall_coords=walls_xy,
        shell_raw_coords=shell_raw_coords,
    )


def run_topology_reconstruction(
    cleanup: CleanupResult,
    trace_collector: ReconstructionTraceCollector | None = None,
    *,
    boundary_run_id: str | None = None,
    boundary_map_input_id: int | None = None,
    boundary_project_id: int | None = None,
    boundary_sink: BoundaryTraceSink | None = None,
) -> ReconstructionResult:
    """Convert miners/extensions from ``CleanupResult`` to ``asteroid_*_field``."""

    return reconstruct_after_cleanup(
        cleaned_cells=cleanup.cleaned_cells,
        original_cells=cleanup.original_cells,
        removed_building_cells=cleanup.removed_building_cells,
        wall_coords=cleanup.wall_coords,
        bbox_bounds=cleanup.bbox_bounds,
        trace_collector=trace_collector,
        boundary_run_id=boundary_run_id,
        boundary_map_input_id=boundary_map_input_id,
        boundary_project_id=boundary_project_id,
        boundary_sink=boundary_sink,
    )


def reconstruct_snapshot(
    snapshot: DecodedBlueprintSnapshotDTO,
    *,
    boundary_run_id: str | None = None,
    boundary_sink: BoundaryTraceSink | None = None,
) -> ReconstructionResult:
    """Decode snapshot → cleanup → miner/extension field reconstruction."""

    from shapez2_factory.domain.asteroid_lab.cleanup.pipeline import deconstruct_snapshot

    c = deconstruct_snapshot(snapshot, boundary_run_id=boundary_run_id, boundary_sink=boundary_sink)
    return reconstruct_after_cleanup(
        cleaned_cells=c.cleaned_cells,
        original_cells=c.original_cells,
        removed_building_cells=c.removed_building_cells,
        wall_coords=c.wall_coords,
        bbox_bounds=c.bbox_bounds,
        boundary_run_id=boundary_run_id,
        boundary_map_input_id=snapshot.map_input_id,
        boundary_project_id=snapshot.project_id,
        boundary_sink=boundary_sink,
    )
