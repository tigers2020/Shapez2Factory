"""Inferred shell closure from evidence walls (reconstruction-only flood barrier)."""

from __future__ import annotations

from collections.abc import Iterable

from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.reconstruction.trace import (
    ReconstructionTraceCollector,
    ReconstructionTraceEvent,
)


def _strict_bbox_interior_cells(walls: set[Coord]) -> set[Coord]:
    """Cells strictly inside the axis-aligned bbox of ``walls`` (excl. ``x == 0``).

    Row/column span must not treat these as inferable gaps: otherwise a hole row
    between two wall evidence columns becomes inferred barrier and kills fill.
    """

    if not walls:
        return set()
    xs = [x for x, _ in walls]
    ys = [y for _, y in walls]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    if mx_x - mn_x < 2 or mx_y - mn_y < 2:
        return set()
    out: set[Coord] = set()
    for x in range(mn_x + 1, mx_x):
        if x == 0:
            continue
        for y in range(mn_y + 1, mx_y):
            out.add((x, y))
    return out


def infer_shell_barrier_coords(
    wall_coords: Iterable[Coord],
    bbox_bounds: tuple[int, int, int, int],
    *,
    trace_collector: ReconstructionTraceCollector | None = None,
) -> frozenset[Coord]:
    """Row/column min–max span closure; returns inferred cells only (not in ``wall_coords``).

    ``bbox_bounds`` is the working padded bbox ``(w0, w1, h0, h1)``. Spans are clipped to
    it. ``x == 0`` is never inferred (dense grid gap convention).

    Flood barrier is ``wall_coords ∪`` this function's return set; fill guard uses
    ``wall_coords`` only (see ``pipeline.reconstruct_after_cleanup``).
    """

    w0, w1, h0, h1 = bbox_bounds
    walls: set[Coord] = set(wall_coords)
    skip_infer: set[Coord] = _strict_bbox_interior_cells(walls)

    by_y: dict[int, set[int]] = {}
    by_x: dict[int, set[int]] = {}
    for x, y in walls:
        by_y.setdefault(y, set()).add(x)
        by_x.setdefault(x, set()).add(y)

    closure: set[Coord] = set()
    row_emit_idx = 0
    for y in sorted(by_y.keys()):
        xs = by_y[y]
        if len(xs) < 2 or y < h0 or y > h1:
            continue
        xa, xb = min(xs), max(xs)
        row_new: set[Coord] = set()
        for x in range(xa, xb + 1):
            if x == 0 or x < w0 or x > w1:
                continue
            c = (x, y)
            if c in walls or c in skip_infer or c in closure:
                continue
            closure.add(c)
            row_new.add(c)
        if trace_collector is not None and row_new:
            ek = f"step4_01_shell_row_{row_emit_idx:03d}"
            row_emit_idx += 1
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="shell_row_span",
                    coords=frozenset(row_new),
                    summary_json={
                        "event_key": ek,
                        "trace_event_type": "shell_row_span",
                        "row_y": y,
                        "span_x0": xa,
                        "span_x1": xb,
                    },
                )
            )

    col_emit_idx = 0
    for x in sorted(by_x.keys()):
        ys = by_x[x]
        if x == 0 or x < w0 or x > w1 or len(ys) < 2:
            continue
        ya, yb = min(ys), max(ys)
        col_new: set[Coord] = set()
        for y in range(ya, yb + 1):
            if y < h0 or y > h1:
                continue
            c = (x, y)
            if c in walls or c in skip_infer or c in closure:
                continue
            closure.add(c)
            col_new.add(c)
        if trace_collector is not None and col_new:
            ek = f"step4_02_shell_col_{col_emit_idx:03d}"
            col_emit_idx += 1
            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="shell_col_span",
                    coords=frozenset(col_new),
                    summary_json={
                        "event_key": ek,
                        "trace_event_type": "shell_col_span",
                        "col_x": x,
                        "span_y0": ya,
                        "span_y1": yb,
                    },
                )
            )

    inferred_only = frozenset(closure - walls)
    if trace_collector is not None:
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="inferred_shell_complete",
                coords=inferred_only,
                summary_json={
                    "event_key": "step4_02_shell_inferred_complete",
                    "trace_event_type": "inferred_shell_complete",
                    "inferred_shell_cell_count": len(inferred_only),
                },
            )
        )

    return frozenset(closure)
