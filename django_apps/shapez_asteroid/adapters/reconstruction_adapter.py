"""Reconstruction + cleanup → ``OptimizationInput`` (Sequence 1B)."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Any

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


def _representative_cell_for_server_bucket(cells: list[DecodedCellDTO]) -> DecodedCellDTO:
    """Pick one cell per server tile when multiple raw columns map to the same server coord."""

    if len(cells) == 1:
        return cells[0]

    def sort_key(c: DecodedCellDTO) -> tuple[int, int, int]:
        in_ast = 0 if c.cell_kind in ASTEROID_FIELD_KINDS else 1
        non_tr = 0 if not is_transport_tile(c) else 1
        return (in_ast, non_tr, int(c.x))

    return min(cells, key=sort_key)


def _trace_event(trace_logger: Any | None, **payload: Any) -> None:
    if trace_logger is None:
        return
    event = getattr(trace_logger, "event", None)
    if callable(event):
        event(**payload)


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
    trace_logger: Any | None = None,
) -> OptimizationInput:
    """Single adapter path; greenfield = empty transport, trunk, and protected sets."""

    params = cleanup.server_xy_params
    recon_cells = reconstruction.cells

    by_server: dict[Coord, list[DecodedCellDTO]] = {}
    for cell in recon_cells:
        sc = decoded_cell_to_server_coord(cell, server_xy_params=params)
        by_server.setdefault(sc, []).append(cell)
    layout_by_server: dict[Coord, DecodedCellDTO] = {
        sc: _representative_cell_for_server_bucket(lst) for sc, lst in by_server.items()
    }

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

    asteroid_cells.update(removed_miner_ext_server)
    asteroid_cells -= transport_cells

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

    opt_input = OptimizationInput(
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
    _trace_event(
        trace_logger,
        stage="optimization_input",
        event="optimization_input_summary",
        severity="info",
        source={
            "module": "django_apps.shapez_asteroid.adapters.reconstruction_adapter",
            "function": "build_optimization_input",
        },
        diagnostic={
            "server_xy_params": params,
            "removed_miner_extension_anchor_server_count": len(removed_miner_ext_server),
            "asteroid_cell_count": len(opt_input.asteroid_cells),
            "mineable_cell_count": len(opt_input.mineable_cells),
            "rim_cell_count": len(opt_input.rim_cells),
            "interior_cell_count": len(opt_input.interior_cells),
            "external_void_cell_count": len(opt_input.external_void_cells),
            "existing_transport_cell_count": len(opt_input.existing_transport_cells),
            "existing_trunk_cell_count": len(opt_input.existing_trunk_cells),
            "blocked_cell_count": len(opt_input.blocked_cells),
            "protected_corridor_cell_count": len(opt_input.protected_corridor_cells),
            "topology_node_count": len(opt_input.topology_graph.nodes),
            "topology_edge_count": len(opt_input.topology_graph.edges),
            "bbox": {
                "min_x": opt_input.bbox.min_x,
                "max_x": opt_input.bbox.max_x,
                "min_y": opt_input.bbox.min_y,
                "max_y": opt_input.bbox.max_y,
            },
        },
    )
    sample_limit = int(getattr(trace_logger, "sample_limit", 128)) if trace_logger else 0
    transport_by_coord = {e.coord: e.transport_kind for e in opt_input.existing_transport_cells}
    sample_coords = sorted(
        (
            set(opt_input.asteroid_cells)
            | set(opt_input.external_void_cells)
            | {e.coord for e in opt_input.existing_transport_cells}
            | set(opt_input.blocked_cells)
            | set(opt_input.protected_corridor_cells)
        ),
        key=lambda c: (c.x, c.y),
    )[:sample_limit]
    for coord in sample_coords:
        tk = transport_by_coord.get(coord)
        _trace_event(
            trace_logger,
            stage="optimization_input",
            event="optimization_input_cell_classified",
            source={
                "module": "django_apps.shapez_asteroid.adapters.reconstruction_adapter",
                "function": "build_optimization_input",
            },
            coord={"server_x": coord.x, "server_y": coord.y},
            diagnostic={
                "coord_system": "server_xy",
                "in_asteroid_cells": coord in opt_input.asteroid_cells,
                "in_mineable_cells": coord in opt_input.mineable_cells,
                "in_rim_cells": coord in opt_input.rim_cells,
                "in_interior_cells": coord in opt_input.interior_cells,
                "in_external_void_cells": coord in opt_input.external_void_cells,
                "existing_transport_kind": None if tk is None else tk.value,
                "is_existing_trunk": coord in opt_input.existing_trunk_cells,
                "is_blocked": coord in opt_input.blocked_cells,
                "is_protected": coord in opt_input.protected_corridor_cells,
            },
        )
    return opt_input
