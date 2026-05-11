"""P3-E2: solver layout → lexicographic router inputs (adapter contract, no commit)."""

from __future__ import annotations

from collections.abc import Mapping, Set
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_zone import (
    RouteZone,
    TransportKind,
    build_asteroid_boundary_depth_by_cell,
    build_route_zone_map,
)


@dataclass(frozen=True)
class RouteAdapterInput:
    """Frozen contract: solver / Pass3 state in → :func:`build_route_adapter_output`."""

    mining_map: tuple[dict[str, Any], ...]
    asteroid_cells: frozenset[Coord]
    mineable_cells: frozenset[Coord]
    extractor_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    final_route_cells: frozenset[Coord]
    fixed_output_stub: Coord
    transport_kind: str
    existing_trunk_cells: frozenset[Coord]
    external_goal_cells: frozenset[Coord]
    hard_protected_cells: frozenset[Coord]
    soft_protected_cells: frozenset[Coord]
    bbox_margin: int


@dataclass(frozen=True)
class RouteAdapterOutput:
    """Maps and sets consumed by :func:`find_lexicographic_route` (+ commit guards later)."""

    zone_by_cell: Mapping[Coord, RouteZone]
    allowed_cells: frozenset[Coord]
    blocked_cells: frozenset[Coord]
    start_stub: Coord
    goal_cells: frozenset[Coord]
    existing_trunk_cells: frozenset[Coord]
    protected_cells: frozenset[Coord]
    interior_depth_by_cell: Mapping[Coord, int]


def build_route_adapter_output(inp: RouteAdapterInput) -> RouteAdapterOutput:
    """Derive router sets from :class:`RouteAdapterInput` (pure, no I/O)."""

    zone = build_route_zone_map(
        asteroid_cells=inp.asteroid_cells, mineable_cells=inp.mineable_cells
    )
    depth = build_asteroid_boundary_depth_by_cell(asteroid_cells=inp.asteroid_cells)
    blocked = (
        frozenset(inp.extractor_cells)
        | frozenset(inp.extension_cells)
        | frozenset(inp.hard_protected_cells)
    )
    protected = frozenset(inp.hard_protected_cells) | frozenset(inp.soft_protected_cells)
    seeds: set[Coord] = (
        set(inp.asteroid_cells)
        | set(inp.final_route_cells)
        | {inp.fixed_output_stub}
        | set(inp.external_goal_cells)
        | set(inp.existing_trunk_cells)
    )
    if not seeds:
        seeds.add(inp.fixed_output_stub)
    xs = [c[0] for c in seeds]
    ys = [c[1] for c in seeds]
    m = max(0, inp.bbox_margin)
    x0, x1 = min(xs) - m, max(xs) + m
    y0, y1 = min(ys) - m, max(ys) + m
    allowed: set[Coord] = set()
    for x in range(x0, x1 + 1):
        if x == 0:
            continue
        for y in range(y0, y1 + 1):
            allowed.add((x, y))
    return RouteAdapterOutput(
        zone_by_cell=zone,
        allowed_cells=frozenset(allowed),
        blocked_cells=blocked,
        start_stub=inp.fixed_output_stub,
        goal_cells=frozenset(inp.external_goal_cells),
        existing_trunk_cells=frozenset(inp.existing_trunk_cells),
        protected_cells=protected,
        interior_depth_by_cell=depth,
    )


def route_adapter_input_for_pass3_stub(
    *,
    mining_map_rows: list[dict[str, Any]],
    cells: dict[Coord, dict[str, Any]],
    mineable_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
    fixed_output_stub: Coord,
    anchor: Coord,
    transport_kind: str,
    same_kind_transport_cells: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    bbox_margin: int = 24,
    hard_protected_cells: frozenset[Coord] | None = None,
    soft_protected_cells: frozenset[Coord] | None = None,
) -> RouteAdapterInput:
    """Build :class:`RouteAdapterInput` for one outlet stub → anchor (Pass3 context)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
        EXTENSIONS,
        EXTRACTORS_FLUID,
        EXTRACTORS_SHAPE,
        layout_kind,
    )

    ex: set[Coord] = set()
    ext: set[Coord] = set()
    for c, row in cells.items():
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            ex.add(c)
        elif lk in EXTENSIONS:
            ext.add(c)
    return RouteAdapterInput(
        mining_map=tuple(mining_map_rows),
        asteroid_cells=asteroid_cells,
        mineable_cells=mineable_cells,
        extractor_cells=frozenset(ex),
        extension_cells=frozenset(ext),
        final_route_cells=frozenset(same_kind_transport_cells),
        fixed_output_stub=fixed_output_stub,
        transport_kind=transport_kind,
        existing_trunk_cells=frozenset(trunk_cells),
        external_goal_cells=frozenset({anchor}),
        hard_protected_cells=frozenset(hard_protected_cells or ()),
        soft_protected_cells=frozenset(soft_protected_cells or ()),
        bbox_margin=bbox_margin,
    )


def count_internal_new_transport_steps_on_path(
    path: tuple[Coord, ...],
    *,
    route_zone_map: Mapping[Coord, RouteZone],
    transport_kind: TransportKind,
    existing_transport_cells: Set[Coord],
    placement_candidate_cells: Set[Coord],
) -> int:
    """Sum lex internal-axis steps (interior cells not already carrying transport)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.lexicographic_router import (  # noqa: E501
        _step_deltas,
    )

    if len(path) < 2:
        return 0
    total = 0
    prev: Coord | None = None
    for i, cur in enumerate(path):
        if i == 0:
            prev = None
            continue
        frm = path[i - 1]
        di, _, _, _, _, _ = _step_deltas(
            prev=prev,
            cur=frm,
            nxt=cur,
            route_zone_map=route_zone_map,
            transport_kind=transport_kind,
            existing_transport_cells=existing_transport_cells,
            placement_candidate_cells=placement_candidate_cells,
            congestion_step=0,
            interior_depth_by_cell=None,
        )
        total += di
        prev = frm
    return total
