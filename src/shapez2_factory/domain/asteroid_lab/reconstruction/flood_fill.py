"""External void flood fill from padded bbox border (walkable cells only)."""

from __future__ import annotations

from collections import deque

from shapez2_factory.domain.asteroid_lab.reconstruction.grid import (
    Coord,
    reconstruction_cardinal_neighbors,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.trace import (
    ReconstructionTraceCollector,
    ReconstructionTraceEvent,
)

RECONSTRUCTION_FLOOD_TRACE_BATCH_SIZE = 32


def external_reachable(
    walkable: set[Coord],
    *,
    w0: int,
    w1: int,
    h0: int,
    h1: int,
    include_raw_x_zero: bool = False,
    trace_collector: ReconstructionTraceCollector | None = None,
) -> set[Coord]:
    """Cells in ``walkable`` reachable from the bbox border via 4-neighbor moves within bbox."""

    q: deque[Coord] = deque()
    seen: set[Coord] = set()

    def try_enqueue(x: int, y: int) -> None:
        if x == 0 and not include_raw_x_zero:
            return
        if x < w0 or x > w1 or y < h0 or y > h1:
            return
        c = (x, y)
        if c not in walkable or c in seen:
            return
        seen.add(c)
        q.append(c)

    for x in range(w0, w1 + 1):
        if x == 0 and not include_raw_x_zero:
            continue
        try_enqueue(x, h0)
        try_enqueue(x, h1)
    for y in range(h0, h1 + 1):
        if w0 != 0 or include_raw_x_zero:
            try_enqueue(w0, y)
        if w1 != 0 or include_raw_x_zero:
            try_enqueue(w1, y)

    if trace_collector is not None:
        seed_coords = frozenset(seen)
        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="flood_seed",
                coords=seed_coords,
                summary_json={
                    "event_key": "step4_04_flood_seed",
                    "trace_event_type": "flood_seed",
                    "seed_count": len(seed_coords),
                    "frontier_size": len(q),
                },
            )
        )

        batch_index = 0
        while q:
            batch_new: set[Coord] = set()
            pops = 0
            while pops < RECONSTRUCTION_FLOOD_TRACE_BATCH_SIZE and q:
                x, y = q.popleft()
                pops += 1
                for nx, ny in reconstruction_cardinal_neighbors(
                    x, y, include_raw_x_zero=include_raw_x_zero
                ):
                    if nx == 0 and not include_raw_x_zero:
                        continue
                    if nx < w0 or nx > w1 or ny < h0 or ny > h1:
                        continue
                    c = (nx, ny)
                    if c not in walkable or c in seen:
                        continue
                    seen.add(c)
                    batch_new.add(c)
                    q.append(c)

            trace_collector.append(
                ReconstructionTraceEvent(
                    phase="reconstruction",
                    trace_event_type="flood_batch",
                    coords=frozenset(batch_new),
                    summary_json={
                        "event_key": f"step4_04_flood_batch_{batch_index:03d}",
                        "trace_event_type": "external_flood_batch",
                        "batch_index": batch_index,
                        "batch_size": RECONSTRUCTION_FLOOD_TRACE_BATCH_SIZE,
                        "visited_added_count": len(batch_new),
                        "visited_total": len(seen),
                        "frontier_size": len(q),
                    },
                )
            )
            batch_index += 1

        trace_collector.append(
            ReconstructionTraceEvent(
                phase="reconstruction",
                trace_event_type="flood_complete",
                coords=frozenset(seen),
                summary_json={
                    "event_key": "step4_04_flood_complete",
                    "trace_event_type": "flood_complete",
                    "visited_total": len(seen),
                    "frontier_size": len(q),
                },
            )
        )
        return seen

    while q:
        x, y = q.popleft()
        for nx, ny in reconstruction_cardinal_neighbors(
            x, y, include_raw_x_zero=include_raw_x_zero
        ):
            try_enqueue(nx, ny)

    return seen


__all__ = ["RECONSTRUCTION_FLOOD_TRACE_BATCH_SIZE", "external_reachable"]
