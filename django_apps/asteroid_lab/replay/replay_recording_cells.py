"""Cell conversion helpers for solver runtime replay recording (Phase 9F/9G)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import MaterializedLayoutCells
from django_apps.asteroid_lab.replay.projection_context import (
    ReplayProjectionContext,
    lab_xy_from_server_xy,
)
from django_apps.asteroid_lab.replay.replay_limits import MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayAnnotation,
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayOverlayCell,
)
from django_apps.asteroid_lab.snapshots.server_coords import server_xy_for_raw_xy


def bbox_from_replay_cells(
    full_cells: tuple[ReplayCell, ...] = (),
    overlay_cells: tuple[ReplayOverlayCell, ...] = (),
    cell_delta: tuple[ReplayCellDelta, ...] = (),
) -> ReplayBBox:
    """Derive an inclusive bounding box from any combination of replay cell tuples."""
    xs: list[int] = []
    ys: list[int] = []
    for c in full_cells:
        xs.append(c.x)
        ys.append(c.y)
    for c in overlay_cells:
        xs.append(c.x)
        ys.append(c.y)
    for c in cell_delta:
        xs.append(c.x)
        ys.append(c.y)
    if not xs:
        return ReplayBBox(min_x=0, min_y=0, max_x=0, max_y=0)
    return ReplayBBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def visible_cells_from_loaded_snapshot(
    loaded: LoadedReconstructionSnapshot,
    ctx: ReplayProjectionContext,
    *,
    cap: int = MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME,
) -> tuple[ReplayCell, ...]:
    """Convert reconstruction snapshot cells to replay full_cells (server → Lab).

    Falls back to ``server_xy_for_raw_xy`` when ``DecodedCellDTO.server_x/server_y``
    are None, mirroring the behaviour of ``reconstruction_adapter._server_xy``.
    """
    out: list[ReplayCell] = []
    min_dense_x, min_raw_y = ctx.server_xy_params
    for cell in loaded.cells:
        if isinstance(cell.server_x, int) and isinstance(cell.server_y, int):
            sx, sy = cell.server_x, cell.server_y
        else:
            try:
                sx, sy = server_xy_for_raw_xy(
                    cell.x, cell.y, min_dense_x=min_dense_x, min_raw_y=min_raw_y
                )
            except Exception:  # noqa: BLE001
                continue
        x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=ctx.server_xy_params)
        out.append(
            ReplayCell(
                x=x,
                y=y,
                kind=str(cell.cell_kind or ""),
                transport=str(cell.transport_kind or ""),
                tile_type=str(cell.tile_type or ""),
                rotation=int(cell.rotation or 0),
            )
        )
        if len(out) >= cap:
            break
    return tuple(out)


def materialized_cells_to_cell_delta(
    layout: MaterializedLayoutCells,
    ctx: ReplayProjectionContext,
    *,
    cap: int = MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME,
) -> tuple[ReplayCellDelta, ...]:
    """Convert materialized transport cells to replay cell_delta entries (server → Lab)."""
    out: list[ReplayCellDelta] = []
    for cell in layout.cells:
        sx, sy = cell.coord
        x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=ctx.server_xy_params)
        out.append(
            ReplayCellDelta(
                x=x,
                y=y,
                kind="transport",
                transport=cell.transport_kind.value,
                tile_type=cell.tile_type,
                rotation=cell.rotation,
                op="set",
            )
        )
        if len(out) >= cap:
            break
    return tuple(out)


def probe_path_to_overlay_cells(
    path: tuple[tuple[int, int], ...],
    ctx: ReplayProjectionContext,
    *,
    cap: int = MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME,
) -> tuple[ReplayOverlayCell, ...]:
    """Convert a route probe path to replay overlay cells (server → Lab)."""
    out: list[ReplayOverlayCell] = []
    for sx, sy in path:
        x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=ctx.server_xy_params)
        out.append(ReplayOverlayCell(x=x, y=y, kind="route_probe", tile_type="route_probe"))
        if len(out) >= cap:
            break
    return tuple(out)


def candidate_occupied_to_overlay_cells(
    candidate: GeneCandidate,
    ctx: ReplayProjectionContext,
    *,
    cap: int = MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME,
) -> tuple[ReplayOverlayCell, ...]:
    """Convert candidate extractor + extensions to replay overlay cells (server → Lab)."""
    coords: list[tuple[int, int]] = [candidate.extractor, *candidate.extensions]
    out: list[ReplayOverlayCell] = []
    for sx, sy in coords:
        x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=ctx.server_xy_params)
        out.append(ReplayOverlayCell(x=x, y=y, kind="candidate", tile_type="candidate"))
        if len(out) >= cap:
            break
    return tuple(out)


def goal_annotations(
    goals: frozenset,
    ctx: ReplayProjectionContext,
) -> tuple[ReplayAnnotation, ...]:
    """Route goals → map annotations (server → Lab, sorted for determinism)."""
    out: list[ReplayAnnotation] = []
    for goal in sorted(goals, key=lambda g: g.coord):
        sx, sy = goal.coord
        x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=ctx.server_xy_params)
        out.append(ReplayAnnotation(x=x, y=y, label=str(goal.goal_kind.value)))
    return tuple(out)


__all__ = [
    "bbox_from_replay_cells",
    "candidate_occupied_to_overlay_cells",
    "goal_annotations",
    "materialized_cells_to_cell_delta",
    "probe_path_to_overlay_cells",
    "visible_cells_from_loaded_snapshot",
]
