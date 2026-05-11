"""Pass1 outer-first placement (Canonical P1-A + P1-B extensions).

Mineable cells are visited perimeter-first. For each extractor site and output
direction, deterministic extension topologies (0..3 tiles, three non-output sides,
extension chains) are tried before falling back to fewer extensions. Every mutation
goes through ``try_commit_pass1_bundle`` (route probe placement gate only; not STEP4).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import step_cardinal
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extension_topology import (  # noqa: E501
    enumerate_extension_topologies,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass12BundleCandidate,
    Pass12LayoutScratch,
    try_commit_pass1_bundle,
)

# Cardinal probe order (deterministic).
_OUTPUT_DIRS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def p1_cheap_void_envelope(
    *,
    mineable_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
    scratch: Pass12LayoutScratch,
    candidate_stub: Coord,
    candidate_blocked: frozenset[Coord],
    candidate_new_transport: frozenset[Coord],
) -> frozenset[Coord]:
    """Finite void tiles allowed for P1 cheap-escape probe (not committed as transport).

    Bounding-box margin ``m`` is ``max(3, min(7, ceil(max(w,h)*0.15)))`` in tile layers from
    the combined footprint (mineable envelope + scratch + candidate).
    """

    pts = (
        set(mineable_cells)
        | set(asteroid_cells)
        | {candidate_stub}
        | set(scratch.transport_cells)
        | set(scratch.blocked_cells)
        | set(candidate_blocked)
        | set(candidate_new_transport)
    )
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    w = x_max - x_min + 1
    h = y_max - y_min + 1
    m = max(3, min(7, math.ceil(max(w, h) * 0.15)))
    out: set[Coord] = set()
    for x in range(x_min - m, x_max + m + 1):
        if x == 0:
            continue
        for y in range(y_min - m, y_max + m + 1):
            out.add((x, y))
    return frozenset(out)


def mineable_outer_first_order(
    mineable_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
) -> tuple[Coord, ...]:
    """Perimeter-adjacent mineable cells first; inner cells after; stable by coordinate."""

    perimeter = frozenset(cells_touching_void(set(asteroid_cells))) & mineable_cells
    inner = mineable_cells - perimeter

    def _coord_key(c: Coord) -> tuple[int, int]:
        """Pass1 outer-first scan을 위한 좌표 정렬키다 (§7 Pass1 placement)."""
        return (c[0], c[1])

    return tuple(sorted(perimeter, key=_coord_key)) + tuple(sorted(inner, key=_coord_key))


def try_place_pass1_outer_bundle(
    *,
    extractor_cell: Coord,
    mineable_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
    scratch: Pass12LayoutScratch,
    is_external: Callable[[Coord], bool],
    bundle_hint: dict[str, Any] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
    extra_transport_block_cells: frozenset[Coord] = frozenset(),
    placement_transport_blocked_counter: list[int] | None = None,
) -> bool:
    """Try output directions in order; commit at most one bundle via ``try_commit_pass1_bundle``."""

    if extractor_cell in scratch.blocked_cells or extractor_cell in scratch.transport_cells:
        return False
    x, y = extractor_cell
    blocked_for_topo = frozenset(scratch.blocked_cells)
    transport_for_topo = frozenset(scratch.transport_cells)
    for dx, dy in _OUTPUT_DIRS:
        stub_cell = step_cardinal(x, y, dx, dy)
        if stub_cell is None:
            continue
        if stub_cell in scratch.transport_cells or stub_cell in extra_transport_block_cells:
            if placement_transport_blocked_counter is not None:
                placement_transport_blocked_counter[0] += 1
            continue
        if stub_cell in scratch.blocked_cells:
            continue
        topologies = enumerate_extension_topologies(
            extractor_cell,
            (dx, dy),
            mineable_cells,
            blocked_for_topo,
            transport_for_topo,
            max_extensions=3,
        )
        for topo in topologies:
            ext_cells = topo.extension_cells
            blocked_c = frozenset({extractor_cell}) | ext_cells
            new_tr = frozenset({stub_cell})
            void_cells = p1_cheap_void_envelope(
                mineable_cells=mineable_cells,
                asteroid_cells=asteroid_cells,
                scratch=scratch,
                candidate_stub=stub_cell,
                candidate_blocked=blocked_c,
                candidate_new_transport=new_tr,
            )
            candidate = Pass12BundleCandidate(
                blocked_cells=blocked_c,
                new_transport=new_tr,
                stub_cell=stub_cell,
                extractor_cell=extractor_cell,
                extension_facings=topo.facings,
                extractor_output_dir=(dx, dy),
                p1_cheap_void_cells=void_cells,
                placement_pass="pass1",
            )
            if try_commit_pass1_bundle(
                scratch,
                candidate,
                is_external=is_external,
                bundle_hint=bundle_hint,
                replay_events=replay_events,
            ):
                return True
    return False


def run_pass1_outer_placement_mvp(
    *,
    mineable_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
    scratch: Pass12LayoutScratch,
    is_external: Callable[[Coord], bool],
    existing_layout_analysis: Mapping[str, Any] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
    extra_transport_block_cells: frozenset[Coord] = frozenset(),
    placement_transport_blocked_counter: list[int] | None = None,
) -> int:
    """Outer-first Pass1 sweep; returns how many extractors were committed."""

    ela_sk = None
    if existing_layout_analysis is not None:
        raw = existing_layout_analysis.get("source_kind")
        if isinstance(raw, str):
            ela_sk = raw
    placed = 0
    for cell in mineable_outer_first_order(mineable_cells, asteroid_cells):
        if cell not in mineable_cells:
            continue
        if cell in scratch.blocked_cells or cell in scratch.transport_cells:
            continue
        hint: dict[str, Any] = {"pass": "p1_outer_mvp", "extractor_cell": cell}
        if ela_sk is not None:
            hint["ela_source_kind"] = ela_sk
        if try_place_pass1_outer_bundle(
            extractor_cell=cell,
            mineable_cells=mineable_cells,
            asteroid_cells=asteroid_cells,
            scratch=scratch,
            is_external=is_external,
            bundle_hint=hint,
            replay_events=replay_events,
            extra_transport_block_cells=extra_transport_block_cells,
            placement_transport_blocked_counter=placement_transport_blocked_counter,
        ):
            placed += 1
    return placed
