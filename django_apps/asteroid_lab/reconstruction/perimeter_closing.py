"""Chebyshev (8-neighbor) perimeter closing for flood barriers (reconstruction-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.reconstruction.shell import _strict_bbox_interior_cells
from django_apps.asteroid_lab.reconstruction.trace import (
    ReconstructionTraceCollector,
    ReconstructionTraceEvent,
)


def _in_working_bbox(x: int, y: int, w0: int, w1: int, h0: int, h1: int) -> bool:
    if x == 0:
        return False
    return w0 <= x <= w1 and h0 <= y <= h1


def chebyshev_close_barrier(
    barrier_xy: set[Coord],
    bbox_bounds: tuple[int, int, int, int],
    *,
    wall_coords: set[Coord],
    trace_collector: ReconstructionTraceCollector | None = None,
) -> set[Coord]:
    """Seal diagonal 1-cell perimeter gaps without filling strict interior holes.

    For each diagonal barrier pair, add the two cardinal corner cells between them
    unless the corner lies in ``_strict_bbox_interior_cells(wall_coords)`` (same
    rule as inferred row/column shell).
    """

    w0, w1, h0, h1 = bbox_bounds
    skip_infer = _strict_bbox_interior_cells(wall_coords)
    closed = set(barrier_xy)
    added: set[Coord] = set()
    barrier_list = tuple(barrier_xy)

    for x1, y1 in barrier_list:
        for x2, y2 in barrier_list:
            if x1 >= x2 and (x1 != x2 or y1 >= y2):
                continue
            if abs(x1 - x2) != 1 or abs(y1 - y2) != 1:
                continue
            for cx, cy in ((x1, y2), (x2, y1)):
                if not _in_working_bbox(cx, cy, w0, w1, h0, h1):
                    continue
                c = (cx, cy)
                if c in closed or c in skip_infer:
                    continue
                closed.add(c)
                added.add(c)

    if trace_collector is not None and added:
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="perimeter_close",
                coords=frozenset(added),
                summary_json={
                    "event_key": "step4_02_perimeter_close",
                    "trace_event_type": "perimeter_close",
                    "perimeter_closed_cell_count": len(added),
                    "barrier_cell_count_after": len(closed),
                },
            )
        )

    return closed
