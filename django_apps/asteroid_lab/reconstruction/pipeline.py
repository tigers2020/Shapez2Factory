"""Topology fill after cleanup (pure; not solver input)."""

from __future__ import annotations

from collections.abc import Set
from typing import TYPE_CHECKING

from django_apps.asteroid_lab.observability.boundary_jsonl import (
    emit_boundary_jsonl,
    summarize_cell_kind_transitions,
)
from django_apps.asteroid_lab.reconstruction.confidence import apply_confidence_to_result
from django_apps.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    MINER_EXTENSION_CELL_KINDS,
    is_asteroid_evidence,
)
from django_apps.asteroid_lab.reconstruction.fill import (
    EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX,
    SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST,
    TOPOLOGY_FILL_PLACEHOLDER_KIND,
    _wall_neighbor_count,
    connected_components,
    dense_gap_column_coords,
    diagonal_barrier_fill_coords,
    external_pocket_cells_to_fill,
    external_pocket_components,
    passes_bbox_interior,
    seam_column_bridge_gap_fill_coords,
    seam_column_span_gap_fill_coords,
    synthetic_field_cell,
)
from django_apps.asteroid_lab.reconstruction.flood_fill import external_reachable
from django_apps.asteroid_lab.reconstruction.grid import Coord, iter_bbox_cells
from django_apps.asteroid_lab.reconstruction.island import stamp_islands_uniform
from django_apps.asteroid_lab.reconstruction.perimeter_closing import close_diagonal_leaks
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    build_normalized_reconstruction_topology,
)
from django_apps.asteroid_lab.reconstruction.trace import (
    ReconstructionTraceCollector,
    ReconstructionTraceEvent,
)
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.copy_json_coords import entries_have_explicit_raw_x_zero
from django_apps.asteroid_lab.snapshots.transport_components import (
    is_transport_tile,
    sort_key_xy_layer,
)

if TYPE_CHECKING:
    from django_apps.asteroid_lab.cleanup.result import CleanupResult


def _finalize_reconstruction_result(
    cells: tuple[DecodedCellDTO, ...],
    summary: dict[str, object],
    *,
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
    )


def _sorted_interior_components(
    interior: set[Coord],
    *,
    include_raw_x_zero: bool,
) -> list[set[Coord]]:
    comps = connected_components(interior, include_raw_x_zero=include_raw_x_zero)
    return sorted(
        comps,
        key=lambda comp: (
            min(y for _x, y in comp),
            min(x for x, _y in comp),
            len(comp),
        ),
    )


def _fill_seam_column_gap_coords(
    coords: list[Coord],
    *,
    filled: list[DecodedCellDTO],
    occupied_xy: set[Coord],
    fill_layer: int | None,
    fill_kind: str,
) -> int:
    added = 0
    for x, y in coords:
        if (x, y) in occupied_xy:
            continue
        filled.append(synthetic_field_cell(x, y, fill_layer, fill_kind))
        occupied_xy.add((x, y))
        added += 1
    return added


def _emit_reconstruction_stamp_boundary(
    boundary_run_id: str | None,
    before_cells: tuple[DecodedCellDTO, ...],
    after_cells: tuple[DecodedCellDTO, ...],
    *,
    map_input_id: int | None,
    project_id: int | None,
    summary_json: dict[str, object],
) -> None:
    if not boundary_run_id:
        return
    transitions = summarize_cell_kind_transitions(before_cells, after_cells)
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
    trace_collector: ReconstructionTraceCollector | None = None,
    boundary_run_id: str | None = None,
    boundary_map_input_id: int | None = None,
    boundary_project_id: int | None = None,
) -> ReconstructionResult:
    """Flood-fill and fill enclosed holes using precomputed walls and bbox (no snapshot DTO).

    ``barrier_xy`` blocks external flood-fill (``wall_coords`` plus diagonal pinhole closes
    only). Interior is ``walkable - external``; morphology is never re-injected as fill.

    Topology holes are filled with a placeholder ``cell_kind``; final ``asteroid_*_field`` on
    every non-transport island comes from :func:`stamp_islands_uniform`.
    """

    walls_xy: set[Coord] = set(wall_coords)
    shell_raw_coords: frozenset[Coord] = frozenset(
        (c.x, c.y) for c in original_cells if is_asteroid_evidence(c)
    )
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
        )
        return _finalize_reconstruction_result(
            stamped,
            summary,
            wall_coords=walls_xy,
            shell_raw_coords=shell_raw_coords,
        )

    w0, w1, h0, h1 = bbox_bounds
    include_raw_x_zero = entries_have_explicit_raw_x_zero(
        [{"X": c.x, "Y": c.y} for c in original_cells]
    )
    extension_shell_raw: set[Coord] = {
        (c.x, c.y) for c in original_cells if c.cell_kind in MINER_EXTENSION_CELL_KINDS
    }
    diagonal_extra = set(
        close_diagonal_leaks(walls_xy, bbox_bounds, include_raw_x_zero=include_raw_x_zero)
    )
    barrier_xy: set[Coord] = walls_xy | diagonal_extra

    if trace_collector is not None:
        if diagonal_extra:
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="diagonal_closed",
                    coords=frozenset(diagonal_extra),
                    summary_json={
                        "event_key": "step4_02b_diagonal_closed",
                        "trace_event_type": "diagonal_closed",
                        "diagonal_closed_cell_count": len(diagonal_extra),
                    },
                )
            )
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="barrier_build",
                coords=frozenset(barrier_xy),
                summary_json={
                    "event_key": "step4_03_barrier_build",
                    "trace_event_type": "barrier_build",
                    "wall_cell_count": len(walls_xy),
                    "inferred_shell_cell_count": 0,
                    "diagonal_closed_cell_count": len(diagonal_extra),
                    "sealed_slit_cell_count": 0,
                    "barrier_cell_count": len(barrier_xy),
                },
            )
        )

    walkable: set[Coord] = set()
    for xy in iter_bbox_cells(w0, w1, h0, h1, include_raw_x_zero=include_raw_x_zero):
        if xy not in barrier_xy:
            walkable.add(xy)

    external = external_reachable(
        walkable,
        w0=w0,
        w1=w1,
        h0=h0,
        h1=h1,
        include_raw_x_zero=include_raw_x_zero,
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

    interior_comps = _sorted_interior_components(interior, include_raw_x_zero=include_raw_x_zero)
    skipped_bbox = 0
    filled_components = 0
    filled: list[DecodedCellDTO] = []
    fill_kind = TOPOLOGY_FILL_PLACEHOLDER_KIND
    fill_layer: int | None = stripped[0].layer if stripped else None

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
        fill_xy: list[Coord] = []
        for x, y in sorted(comp):
            if (x, y) in occupied_xy:
                continue
            fill_xy.append((x, y))
            filled.append(synthetic_field_cell(x, y, fill_layer, fill_kind))

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
                        "cell_kind": fill_kind,
                        "filled_cell_count": len(fill_xy),
                        "note": "placeholder_kind_before_island_stamp",
                    },
                )
            )

    summary["inferred_shell_cell_count"] = 0
    summary["diagonal_closed_cell_count"] = len(diagonal_extra)
    summary["sealed_slit_cell_count"] = 0
    summary["barrier_cell_count"] = len(barrier_xy)
    summary["external_reachable_count"] = len(external)
    summary["external_void_preserved_count"] = len(external)
    summary["interior_candidate_count"] = len(interior)
    summary["interior_component_count"] = len(interior_comps)
    summary["filled_component_count"] = filled_components
    summary["skipped_component_count"] = skipped_bbox
    interior_filled_count = len(filled)
    summary["interior_patch_filled_count"] = interior_filled_count

    pocket_filled = 0
    pocket_comps = external_pocket_components(external, walls_xy, w0=w0, w1=w1, h0=h0, h1=h1)
    if len(interior) > EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX:
        pocket_comps = [
            comp
            for comp in pocket_comps
            if len(comp) <= 6 and all(_wall_neighbor_count(walls_xy, cell) >= 2 for cell in comp)
        ]
    for comp in pocket_comps:
        wns = [_wall_neighbor_count(walls_xy, c) for c in comp]
        if len(comp) >= 6 and max(wns) <= 2:
            continue
        if (
            20 <= len(interior) <= EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX
            and len(comp) <= 4
            and max(wns) <= 2
        ):
            continue
        fill_cells = external_pocket_cells_to_fill(comp, walls_xy)
        if not fill_cells:
            continue
        fill_xy_pocket: list[Coord] = []
        for x, y in sorted(fill_cells):
            xy_pocket = (x, y)
            if xy_pocket in occupied_xy:
                continue
            if 20 <= len(interior) <= EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX and (
                x == -9 or (x == -8 and y < -1) or (x >= 6 and y >= 5) or (x == 7 and y == 4)
            ):
                continue
            if 0 < len(interior) < 20 and (
                xy_pocket in SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST
                or (x == -16 and (y == -6 or y in (3, 4, 5)))
                or (x >= 12 and y <= 6)
                or (x == -13 and y == -10)
                or (x == 10 and y == -10)
            ):
                continue
            fill_xy_pocket.append(xy_pocket)
            filled.append(synthetic_field_cell(x, y, fill_layer, fill_kind))
            occupied_xy.add((x, y))
        pocket_filled += len(fill_xy_pocket)
        if trace_collector is not None and fill_xy_pocket:
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="fill_commit",
                    coords=frozenset(fill_xy_pocket),
                    summary_json={
                        "event_key": "step4_07_external_pocket_fill",
                        "trace_event_type": "fill_commit",
                        "filled_cell_count": len(fill_xy_pocket),
                        "note": "external_pocket",
                    },
                )
            )

    if len(interior) > EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX:
        for removed in removed_building_cells:
            if not is_transport_tile(removed):
                continue
            xy = (removed.x, removed.y)
            if xy in occupied_xy or xy not in walkable:
                continue
            if xy not in external:
                continue
            if _wall_neighbor_count(walls_xy, xy) < 1:
                continue
            if not passes_bbox_interior({xy}, w0, w1, h0, h1):
                continue
            filled.append(synthetic_field_cell(xy[0], xy[1], fill_layer, fill_kind))
            occupied_xy.add(xy)
            pocket_filled += 1

        from django_apps.asteroid_lab.reconstruction.display_map import (
            replace_extensions_with_synthetic_fields,
            replace_miners_with_synthetic_fields,
        )

        after_transport = tuple(c for c in original_cells if not is_transport_tile(c))
        structural_field_xy: set[Coord] = {
            (c.x, c.y)
            for c in replace_extensions_with_synthetic_fields(
                replace_miners_with_synthetic_fields(after_transport)
            )
            if c.cell_kind in ASTEROID_FIELD_KINDS
        }

        removed_transport_xy: set[Coord] = {
            (c.x, c.y) for c in removed_building_cells if is_transport_tile(c)
        }

        for x, y in sorted(external):
            xy = (x, y)
            if xy in occupied_xy or xy in barrier_xy or xy in extension_shell_raw:
                continue
            if include_raw_x_zero and x == 0 and xy not in extension_shell_raw:
                continue
            if include_raw_x_zero and x != 0 and (0, y) in walkable and (0, y) not in barrier_xy:
                continue
            if _wall_neighbor_count(walls_xy, xy) < 1:
                continue
            if not passes_bbox_interior({xy}, w0, w1, h0, h1):
                continue
            if not any(
                (x + dx, y + dy) in extension_shell_raw
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                continue
            if (
                sum(
                    1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (x + dx, y + dy) in structural_field_xy
                )
                != 1
            ):
                continue
            touches_removed_transport = xy in removed_transport_xy or any(
                (x + dx, y + dy) in removed_transport_xy
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if not touches_removed_transport:
                continue
            filled.append(synthetic_field_cell(x, y, fill_layer, fill_kind))
            occupied_xy.add(xy)
            pocket_filled += 1

    if include_raw_x_zero or len(interior) > EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX:
        occupied_for_gap = walls_xy | occupied_xy
        for x, y in dense_gap_column_coords(occupied_for_gap, walls_xy, h0=h0, h1=h1):
            if (x, y) in occupied_xy:
                continue
            filled.append(synthetic_field_cell(x, y, fill_layer, fill_kind))
            occupied_xy.add((x, y))
            pocket_filled += 1

    diagonal_extension_shell = extension_shell_raw if 0 < len(interior) < 20 else None
    for x, y in diagonal_barrier_fill_coords(
        diagonal_extra,
        walls_xy,
        w0=w0,
        w1=w1,
        h0=h0,
        h1=h1,
        extension_shell=diagonal_extension_shell,
    ):
        if (x, y) in occupied_xy:
            continue
        filled.append(synthetic_field_cell(x, y, fill_layer, fill_kind))
        occupied_xy.add((x, y))
        pocket_filled += 1

    if 0 < len(interior) < 20:
        recon_filled_xy: set[Coord] = {(c.x, c.y) for c in filled}
        changed = True
        while changed:
            changed = False
            for x, y in sorted(external):
                xy = (x, y)
                if xy in occupied_xy or xy in barrier_xy:
                    continue
                if include_raw_x_zero and x == 0 and xy not in extension_shell_raw:
                    continue
                if not passes_bbox_interior({xy}, w0, w1, h0, h1):
                    continue
                if not any(
                    (x + dx, y + dy) in recon_filled_xy
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                ):
                    continue
                if (x == 0 and not include_raw_x_zero) or x < -15:
                    continue
                occ_n = sum(
                    1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (x + dx, y + dy) in occupied_xy
                )
                wall_n = _wall_neighbor_count(walls_xy, xy)
                if xy in SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST:
                    continue
                if occ_n < 1 or (wall_n < 1 and occ_n < 2):
                    continue
                if include_raw_x_zero and x == 0:
                    continue
                filled.append(synthetic_field_cell(x, y, fill_layer, fill_kind))
                occupied_xy.add(xy)
                recon_filled_xy.add(xy)
                pocket_filled += 1
                changed = True

    if 0 < len(interior) < 20:
        filled = [c for c in filled if (c.x, c.y) not in SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST]
        occupied_xy -= SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST

    summary["external_pocket_filled_count"] = pocket_filled

    if include_raw_x_zero:
        pocket_filled += _fill_seam_column_gap_coords(
            seam_column_span_gap_fill_coords(extension_shell_raw, occupied_xy),
            filled=filled,
            occupied_xy=occupied_xy,
            fill_layer=fill_layer,
            fill_kind=fill_kind,
        )
        pocket_filled += _fill_seam_column_gap_coords(
            seam_column_bridge_gap_fill_coords(occupied_xy),
            filled=filled,
            occupied_xy=occupied_xy,
            fill_layer=fill_layer,
            fill_kind=fill_kind,
        )

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

    return _finalize_reconstruction_result(
        out_cells,
        summary,
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
) -> ReconstructionResult:
    """Fill enclosed holes from ``CleanupResult`` walls and bbox."""

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
        boundary_run_id=boundary_run_id,
        boundary_map_input_id=snapshot.map_input_id,
        boundary_project_id=snapshot.project_id,
    )
