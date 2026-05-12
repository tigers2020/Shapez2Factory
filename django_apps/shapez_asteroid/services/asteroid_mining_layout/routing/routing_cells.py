"""Shared mining-map cell helpers: layout_kind, routing jobs, blocked extractor bodies.

Kept dependency-light (geometry + extraction rotation only) so ``final_validation`` and
``step4_merge_routing`` can share one implementation without import cycles.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

__all__ = [
    "EXTENSIONS",
    "EXTRACTORS_FLUID",
    "EXTRACTORS_SHAPE",
    "blocked_cells",
    "collect_routing_jobs",
    "layout_kind",
    "mineable_and_asteroid_coords",
    "transport_kind_for_extractor",
    "want_role",
]


def layout_kind(row: dict[str, Any]) -> str | None:
    """Normalize ``row['layout_kind']`` to ``str`` for routing / validation (§9, §15)."""

    lk = row.get("layout_kind")
    return str(lk) if lk is not None else None


def mineable_and_asteroid_coords(
    final_mining_map: list[dict[str, Any]],
) -> tuple[frozenset[Coord], frozenset[Coord]]:
    """Mineable placement sites and full asteroid patch coords from a reconstructed final map."""

    mineable: set[Coord] = set()
    asteroid: set[Coord] = set()
    for row in final_mining_map:
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        role = row.get("role")
        lk = layout_kind(row)
        c = (x, y)
        if role == "inferred":
            asteroid.add(c)
            mineable.add(c)
        elif role == "occupied":
            asteroid.add(c)
            if lk == "asteroid_field":
                mineable.add(c)
    return frozenset(mineable), frozenset(asteroid)


def transport_kind_for_extractor(row: dict[str, Any]) -> str | None:
    """Map extractor ``layout_kind`` to solver transport kind (belt vs pipe)."""

    lk = layout_kind(row)
    if lk in EXTRACTORS_SHAPE:
        return "shape_belt"
    if lk in EXTRACTORS_FLUID:
        return "fluid_pipe"
    return None


def want_role(transport_kind: str) -> str:
    """Map transport kind string to mining_map role (``belt`` / ``pipe``)."""

    if transport_kind == "shape_belt":
        return "belt"
    if transport_kind == "fluid_pipe":
        return "pipe"
    raise ValueError(f"unknown transport_kind {transport_kind!r}")


def blocked_cells(cells: dict[Coord, dict[str, Any]]) -> set[Coord]:
    """Cells occupied by extractor/extension bodies that routes must not cross (§9)."""

    blocked: set[Coord] = set()
    for c, row in cells.items():
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID | EXTENSIONS:
            blocked.add(c)
    return blocked


def collect_routing_jobs(
    cells: dict[Coord, dict[str, Any]],
) -> list[tuple[Coord, Coord, str, str | None]]:
    """Collect STEP4/Pass3 jobs: extractor cell, stub, transport kind, placement_id."""

    jobs: list[tuple[Coord, Coord, str, str | None]] = []
    for c, row in cells.items():
        lk = layout_kind(row)
        if lk not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            continue
        tk = transport_kind_for_extractor(row)
        if tk is None:
            continue
        raw_r = row.get("r")
        if not isinstance(raw_r, int):
            continue
        stub = shape_miner_output_cell(c, raw_r)
        if stub is None:
            continue
        st = cells.get(stub)
        wr = want_role(tk)
        if st is None or st.get("role") != wr:
            continue
        pid_raw = row.get("placement_id")
        pid = str(pid_raw) if isinstance(pid_raw, str) else None
        jobs.append((c, stub, tk, pid))
    jobs.sort(key=lambda j: (j[1][1], j[1][0], j[0][1], j[0][0]))
    return jobs
