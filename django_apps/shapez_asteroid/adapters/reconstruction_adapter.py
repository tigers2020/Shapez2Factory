"""Reconstruction + cleanup → ``OptimizationInput`` (Sequence 1B)."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.server_coords import (
    coerce_server_axis_int,
    server_xy_for_layout_line_xy,
    server_xy_for_raw_xy,
)
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile
from django_apps.shapez_asteroid.optimization.coords import BBox, Coord, neighbors4_server
from django_apps.shapez_asteroid.optimization.dto import (
    ExistingTransportCell,
    OptimizationInput,
    RouteGoal,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from django_apps.shapez_asteroid.optimization.enums import (
    EdgeKind,
    RouteGoalKind,
    TopologyNodeKind,
    TransportKind,
)


def _lex_key(c: Coord) -> tuple[int, int]:
    return (c.x, c.y)


def _canonical_edge(a: Coord, b: Coord, *, cost: int = 1) -> TopologyEdge:
    if _lex_key(a) <= _lex_key(b):
        return TopologyEdge(a=a, b=b, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)
    return TopologyEdge(a=b, b=a, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)


def decoded_cell_to_server_coord(
    cell: DecodedCellDTO,
    *,
    server_xy_params: tuple[int, int] | None,
) -> Coord:
    sx = coerce_server_axis_int(cell.server_x)
    sy = coerce_server_axis_int(cell.server_y)
    if sx is not None and sy is not None:
        return Coord(sx, sy)
    if server_xy_params is not None:
        raw_x = int(cell.x)
        raw_y = int(cell.y)
        max_dx, min_y = int(server_xy_params[0]), int(server_xy_params[1])
        if raw_x == 0:
            # Strict blueprint raw omits x==0; layout/world rows may still use 0 after offsets.
            lx, ly = server_xy_for_layout_line_xy(raw_x, raw_y, max_dense_x=max_dx, min_raw_y=min_y)
            return Coord(lx, ly)
        raw_pair = server_xy_for_raw_xy(
            raw_x,
            raw_y,
            max_dense_x=max_dx,
            min_raw_y=min_y,
        )
        if raw_pair is None:
            raise ValueError(
                "server_xy_for_raw_xy returned None for non-zero raw X "
                f"(raw=({cell.x},{cell.y}) params={server_xy_params!r} "
                f"server=({cell.server_x!r},{cell.server_y!r}))"
            )
        return Coord(raw_pair[0], raw_pair[1])
    raise ValueError(
        "DecodedCellDTO missing server_x/server_y and no server_xy_params for mapping."
    )


def _transport_kind_from_cell(cell: DecodedCellDTO) -> TransportKind:
    if cell.transport_kind == "fluid_pipe":
        return TransportKind.FLUID_PIPE
    return TransportKind.SHAPE_BELT


def _compute_bbox(coords: Iterable[Coord]) -> BBox:
    cs = list(coords)
    if not cs:
        return BBox(0, 0, 0, 0)
    xs = [c.x for c in cs]
    ys = [c.y for c in cs]
    return BBox(min(xs), max(xs), min(ys), max(ys))


def _pad_bbox(b: BBox, pad: int) -> BBox:
    return BBox(b.min_x - pad, b.max_x + pad, b.min_y - pad, b.max_y + pad)


def _external_void_cells(
    bbox: BBox,
    *,
    opaque_coords: frozenset[Coord],
) -> frozenset[Coord]:
    """Flood from bbox boundary through cells not in ``opaque_coords`` (4-neighbor)."""

    bbox_cells = set(bbox.iter_cells())
    ext: set[Coord] = set()
    q: deque[Coord] = deque()
    for c in bbox_cells:
        if c in opaque_coords:
            continue
        on_edge = c.x == bbox.min_x or c.x == bbox.max_x or c.y == bbox.min_y or c.y == bbox.max_y
        if on_edge:
            ext.add(c)
            q.append(c)
    while q:
        cur = q.popleft()
        for nb in neighbors4_server(cur):
            if nb not in bbox_cells or nb in opaque_coords or nb in ext:
                continue
            ext.add(nb)
            q.append(nb)
    return frozenset(ext)


def _build_topology_graph(
    bbox: BBox,
    *,
    asteroid_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
    transport_cells: frozenset[Coord],
    rim_cells: frozenset[Coord],
) -> TopologyGraph:
    nodes: set[TopologyNode] = set()
    edges: set[TopologyEdge] = set()
    for c in bbox.iter_cells():
        if c in transport_cells:
            kind = TopologyNodeKind.TRANSPORT
        elif c in external_void_cells:
            kind = TopologyNodeKind.EXTERNAL_VOID
        elif c in rim_cells:
            kind = TopologyNodeKind.RIM
        elif c in asteroid_cells:
            kind = TopologyNodeKind.ASTEROID_FIELD
        else:
            kind = TopologyNodeKind.EXTERNAL_VOID
        nodes.add(TopologyNode(coord=c, node_kind=kind))
    bbox_set = set(bbox.iter_cells())
    for c in bbox.iter_cells():
        for nb in neighbors4_server(c):
            if nb not in bbox_set:
                continue
            edges.add(_canonical_edge(c, nb))
    return TopologyGraph(nodes=frozenset(nodes), edges=frozenset(edges))


def _route_goals(
    *,
    rim_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
    existing_transport_cells: frozenset[ExistingTransportCell],
    existing_trunk_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
) -> frozenset[RouteGoal]:
    goals: set[RouteGoal] = set()
    void_adj_rim = frozenset(
        rc for rc in rim_cells if any(n in external_void_cells for n in neighbors4_server(rc))
    )
    for rc in sorted(void_adj_rim, key=_lex_key):
        goals.add(
            RouteGoal(
                coord=rc,
                goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
                transport_kind=None,
                priority=20,
                existing_trunk=False,
            )
        )
    for tc in sorted(existing_trunk_cells, key=_lex_key):
        cell = next((e for e in existing_transport_cells if e.coord == tc), None)
        tk = cell.transport_kind if cell is not None else None
        goals.add(
            RouteGoal(
                coord=tc,
                goal_kind=RouteGoalKind.TRUNK_SEED,
                transport_kind=tk,
                priority=0,
                existing_trunk=True,
            )
        )
    for etc in sorted(existing_transport_cells, key=lambda e: _lex_key(e.coord)):
        if etc.coord in existing_trunk_cells:
            continue
        if any(n in asteroid_cells for n in neighbors4_server(etc.coord)):
            goals.add(
                RouteGoal(
                    coord=etc.coord,
                    goal_kind=RouteGoalKind.EXISTING_TRANSPORT_ATTACHMENT,
                    transport_kind=etc.transport_kind,
                    priority=10,
                    existing_trunk=False,
                )
            )
    return frozenset(goals)


def build_optimization_input(
    reconstruction: ReconstructionResult,
    cleanup: CleanupResult,
    *,
    protected_corridor_cells: frozenset[Coord] | None = None,
    blocked_cells: frozenset[Coord] | None = None,
    existing_transport_cells: frozenset[ExistingTransportCell] | None = None,
    existing_trunk_cells: frozenset[Coord] | None = None,
) -> OptimizationInput:
    """Single adapter path; greenfield = empty transport, trunk, and protected sets."""

    params = cleanup.server_xy_params
    recon_cells = reconstruction.cells

    layout_by_server: dict[Coord, DecodedCellDTO] = {}
    for cell in recon_cells:
        sc = decoded_cell_to_server_coord(cell, server_xy_params=params)
        layout_by_server[sc] = cell

    ignored_transport_server = frozenset(
        decoded_cell_to_server_coord(c, server_xy_params=params)
        for c in cleanup.ignored_transport_cells
    )
    removed_miner_ext_server = frozenset(
        decoded_cell_to_server_coord(c, server_xy_params=params)
        for c in cleanup.removed_building_cells
        if c.cell_kind
        in (
            "fluid_miner",
            "fluid_miner_extension",
            "shape_miner",
            "shape_miner_extension",
        )
    )

    asteroid_cells: set[Coord] = set()
    transport_cells: set[Coord] = set()
    for sc, cell in layout_by_server.items():
        if is_transport_tile(cell):
            transport_cells.add(sc)
        elif cell.cell_kind in ASTEROID_FIELD_KINDS:
            asteroid_cells.add(sc)

    mineable_cells = frozenset(asteroid_cells)

    base_coords = (
        set(layout_by_server) | set(ignored_transport_server) | set(removed_miner_ext_server)
    )
    pc = protected_corridor_cells or frozenset()
    bc = blocked_cells or frozenset()
    base_coords |= set(pc) | set(bc)

    et = existing_transport_cells
    if et is None:
        et = frozenset(
            ExistingTransportCell(coord=sc, transport_kind=_transport_kind_from_cell(cell))
            for sc, cell in layout_by_server.items()
            if is_transport_tile(cell)
        )
    trunk = existing_trunk_cells if existing_trunk_cells is not None else frozenset()
    trunk = frozenset(c for c in trunk if c in {e.coord for e in et})

    base_coords |= {e.coord for e in et} | set(trunk)

    bbox = _pad_bbox(_compute_bbox(base_coords), 1)
    opaque = frozenset(asteroid_cells | transport_cells)
    external_void_cells = _external_void_cells(bbox, opaque_coords=opaque)

    rim_cells = frozenset(
        ac for ac in asteroid_cells if any(n in external_void_cells for n in neighbors4_server(ac))
    )
    interior_cells = frozenset(ac for ac in asteroid_cells if ac not in rim_cells)

    topology = _build_topology_graph(
        bbox,
        asteroid_cells=frozenset(asteroid_cells),
        external_void_cells=external_void_cells,
        transport_cells=frozenset(transport_cells),
        rim_cells=rim_cells,
    )
    route_goals = _route_goals(
        rim_cells=rim_cells,
        external_void_cells=external_void_cells,
        existing_transport_cells=et,
        existing_trunk_cells=trunk,
        asteroid_cells=frozenset(asteroid_cells),
    )

    return OptimizationInput(
        asteroid_cells=frozenset(asteroid_cells),
        mineable_cells=mineable_cells,
        rim_cells=rim_cells,
        interior_cells=interior_cells,
        external_void_cells=external_void_cells,
        route_goals=route_goals,
        existing_transport_cells=et,
        existing_trunk_cells=trunk,
        protected_corridor_cells=pc,
        blocked_cells=bc,
        topology_graph=topology,
        bbox=bbox,
    )
