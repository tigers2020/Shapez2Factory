"""Reconstruction snapshot → OptimizationInput (Sequence 1B / Solver Runtime PR1B)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord, neighbors4_server
from django_apps.asteroid_lab.optimization.enums import EdgeKind, TopologyNodeKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    ExistingTransportCell,
    OptimizationInput,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    LoadedReconstructionSnapshot,
    loaded_reconstruction_snapshot_from_result,
)
from django_apps.asteroid_lab.reconstruction.evidence import (
    evidence_field_kind,
    inferred_field_kind_from_removed_miner_extension,
    is_asteroid_evidence,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.server_coords import server_xy_for_raw_xy
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile


def _server_xy(cell: DecodedCellDTO, params: tuple[int, int] | None) -> Coord:
    sx, sy = cell.server_x, cell.server_y
    if isinstance(sx, int) and isinstance(sy, int):
        return (sx, sy)
    if params is not None:
        return server_xy_for_raw_xy(
            cell.x,
            cell.y,
            min_dense_x=params[0],
            min_raw_y=params[1],
        )
    msg = "DecodedCellDTO.server_x/server_y missing and ReconstructionResult.server_xy_params unset"
    raise ValueError(msg)


def mineable_field_kind(cell: DecodedCellDTO) -> str | None:
    """§0.3 adapter-only field kind for mineable sets (does not mutate ``cell``)."""

    inferred = inferred_field_kind_from_removed_miner_extension(cell)
    if inferred is not None:
        return inferred
    return evidence_field_kind(cell)


def _parse_transport_kind(raw: str) -> TransportKind:
    for member in TransportKind:
        if member.value == raw:
            return member
    return TransportKind.NONE


def _topology_node_kind(
    cell: DecodedCellDTO, sv: Coord, mineable: frozenset[Coord]
) -> TopologyNodeKind:
    if is_transport_tile(cell):
        return TopologyNodeKind.TRANSPORT
    if sv in mineable:
        return TopologyNodeKind.ASTEROID_FIELD
    if is_asteroid_evidence(cell):
        return TopologyNodeKind.ASTEROID_FIELD
    return TopologyNodeKind.UNKNOWN


def _blocked_shell(cell: DecodedCellDTO, sv: Coord, mineable: frozenset[Coord]) -> bool:
    if sv in mineable or is_transport_tile(cell):
        return False
    if cell.cell_kind == "unknown" and str(cell.tile_type).startswith("UnknownTile_"):
        return True
    return False


def build_topology_graph(
    cells: tuple[DecodedCellDTO, ...],
    *,
    mineable: frozenset[Coord],
    server_xy_params: tuple[int, int] | None,
) -> TopologyGraph:
    """Undirected graph over decoded cells using ``neighbors4_server`` adjacency."""

    by_sv: dict[Coord, DecodedCellDTO] = {}
    for c in cells:
        sv = _server_xy(c, server_xy_params)
        by_sv[sv] = c

    nodes: set[TopologyNode] = set()
    for sv, c in by_sv.items():
        nodes.add(TopologyNode(coord=sv, node_kind=_topology_node_kind(c, sv, mineable)))

    edges: set[TopologyEdge] = set()
    for sv in by_sv:
        for nb in neighbors4_server(sv):
            if nb not in by_sv:
                continue
            e1 = TopologyEdge(a=sv, b=nb, edge_kind=EdgeKind.CARDINAL, traversal_cost=1)
            e2 = TopologyEdge(a=nb, b=sv, edge_kind=EdgeKind.CARDINAL, traversal_cost=1)
            edges.add(e1)
            edges.add(e2)

    return TopologyGraph(nodes=frozenset(nodes), edges=frozenset(edges))


def _bbox_from_coords(coords: frozenset[Coord]) -> BBox:
    if not coords:
        return BBox(0, 0, 0, 0)
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return BBox(min(xs), max(xs), min(ys), max(ys))


def optimization_input_from_loaded_snapshot(
    snapshot: LoadedReconstructionSnapshot,
) -> OptimizationInput:
    """Map Phase A snapshot to ``OptimizationInput`` (Server X/Y only, §0.3 at adapter)."""

    cells = snapshot.cells
    params = snapshot.server_xy_params
    by_sv: dict[Coord, DecodedCellDTO] = {}
    for c in cells:
        sv = _server_xy(c, params)
        by_sv[sv] = c

    mineable: set[Coord] = set()
    for sv, c in by_sv.items():
        if mineable_field_kind(c) is not None:
            mineable.add(sv)

    asteroid_evidence: set[Coord] = set(mineable)
    for sv, c in by_sv.items():
        if is_asteroid_evidence(c):
            asteroid_evidence.add(sv)

    transport_cells_list: list[ExistingTransportCell] = []
    for sv, c in by_sv.items():
        if not is_transport_tile(c):
            continue
        tk = _parse_transport_kind(c.transport_kind)
        transport_cells_list.append(ExistingTransportCell(coord=sv, transport_kind=tk))

    mineable_f = frozenset(mineable)
    blocked: set[Coord] = set()
    for sv, c in by_sv.items():
        if _blocked_shell(c, sv, mineable_f):
            blocked.add(sv)

    rim: set[Coord] = set()
    interior: set[Coord] = set()
    for sv in mineable:
        nbs = neighbors4_server(sv)
        touches_non_mineable = any(n not in mineable for n in nbs)
        if touches_non_mineable:
            rim.add(sv)
        else:
            interior.add(sv)

    all_sv = frozenset(by_sv)
    bbox = _bbox_from_coords(all_sv)
    external_void: set[Coord] = set()
    for sx in range(bbox.min_sx, bbox.max_sx + 1):
        for sy in range(bbox.min_sy, bbox.max_sy + 1):
            ccoord = (sx, sy)
            if ccoord in all_sv:
                continue
            external_void.add(ccoord)

    topo = build_topology_graph(cells, mineable=mineable_f, server_xy_params=params)

    return OptimizationInput(
        asteroid_cells=frozenset(asteroid_evidence),
        mineable_cells=mineable_f,
        rim_cells=frozenset(rim),
        interior_cells=frozenset(interior),
        external_void_cells=frozenset(external_void),
        route_goals=frozenset(),
        existing_transport_cells=frozenset(transport_cells_list),
        existing_trunk_cells=frozenset(),
        protected_corridor_cells=frozenset(),
        blocked_cells=frozenset(blocked),
        topology_graph=topo,
        bbox=bbox,
    )


def optimization_input_from_reconstruction(result: ReconstructionResult) -> OptimizationInput:
    """Thin wrapper over :func:`optimization_input_from_loaded_snapshot`."""

    snap = loaded_reconstruction_snapshot_from_result(result)
    return optimization_input_from_loaded_snapshot(snap)
