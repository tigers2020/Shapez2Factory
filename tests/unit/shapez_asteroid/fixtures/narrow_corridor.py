"""Narrow-corridor optimization fixtures (Sequence 10A).

Geometry: 1-wide bridge cell ``(1, 0)`` between rim extractors at ``(0, 0)`` and ``(2, 0)``.
The bridge may be marked ``protected_corridor_cells`` so the seed ``route_domain`` uses
``RouteClass.NARROW_CORRIDOR`` (see ``RouteDomainSnapshotBuilder``).

Candidate-time probes use only each candidate's own ``occupied_cells`` overlay; incremental
commit re-runs ``run_route_probe`` with the union of prior committed placements and the
current candidate — reproducing reachable-at-pool / blocked-at-commit starvation.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.coords import BBox, Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    Gene,
    Genome,
    OptimizationInput,
    RouteGoal,
    RouteProbeResult,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CardinalDirection,
    EdgeKind,
    RouteGoalKind,
    TopologyNodeKind,
    TransportKind,
)


def _canon_edge(a: Coord, b: Coord, cost: int = 1) -> TopologyEdge:
    if (a.x, a.y) <= (b.x, b.y):
        return TopologyEdge(a=a, b=b, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)
    return TopologyEdge(a=b, b=a, edge_kind=EdgeKind.CARDINAL, traversal_cost=cost)


def narrow_bridge_coords() -> tuple[Coord, Coord, Coord]:
    return Coord(0, 0), Coord(1, 0), Coord(2, 0)


def build_narrow_bridge_optimization_input(
    *,
    protected_bridge: bool = True,
    existing_trunk_overlap: bool = False,
) -> tuple[OptimizationInput, RouteGoal]:
    """Three-cell horizontal strip with optional protected bridge and trunk overlap stub."""

    c0, c1, c2 = narrow_bridge_coords()
    coords = (c0, c1, c2)
    ac = frozenset(coords)
    rim = frozenset({c0, c2})
    mineable = ac
    interior = frozenset({c1})
    ext_void: frozenset[Coord] = frozenset()
    goal = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    bbox = BBox(0, 2, 0, 0)
    nodes = frozenset(
        TopologyNode(coord=c, node_kind=TopologyNodeKind.EXTERNAL_VOID) for c in coords
    )
    edges = frozenset({_canon_edge(c0, c1), _canon_edge(c1, c2)})
    topo = TopologyGraph(nodes=nodes, edges=edges)
    protected = frozenset({c1}) if protected_bridge else frozenset()
    trunk_overlap = frozenset({c1}) if existing_trunk_overlap else frozenset()
    inp = OptimizationInput(
        asteroid_cells=ac,
        mineable_cells=mineable,
        rim_cells=rim,
        interior_cells=interior,
        external_void_cells=ext_void,
        route_goals=frozenset({goal}),
        existing_transport_cells=frozenset(),
        existing_trunk_cells=trunk_overlap,
        protected_corridor_cells=protected,
        blocked_cells=frozenset(),
        topology_graph=topo,
        bbox=bbox,
    )
    return inp, goal


def build_rim_competition_pool(
    inp: OptimizationInput,
    *,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
) -> tuple[tuple[BundleCandidate, ...], Genome]:
    """Two rim extractors compete for the same bridge.

    Each bundle carries a **candidate-stage** probe snapshot (solo generation), modeled here
    as reachable along ``(bridge, goal)`` even when a literal solo ``run_route_probe`` would
    not match that contract. Incremental commit always re-probes against the latest
    ``route_domain`` and merged ``occupied_cells`` overlay.
    """

    c0, c1, c2 = narrow_bridge_coords()
    goal = next(iter(sorted(inp.route_goals, key=lambda z: (z.coord.x, z.coord.y))))
    solo_path = (c1, c2)
    stale_ok = RouteProbeResult(
        reachable=True,
        path=solo_path,
        cost=len(solo_path),
        expanded_nodes=len(solo_path),
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )

    def _bundle(
        cid: str,
        occupied: frozenset[Coord],
        probe: RouteProbeResult,
    ) -> BundleCandidate:
        extractor = min(occupied, key=lambda z: (z.x, z.y))
        extensions = tuple(sorted(occupied - {extractor}, key=lambda z: (z.x, z.y)))
        return BundleCandidate(
            candidate_id=cid,
            pattern_id="narrow_bridge",
            topology_signature="narrow_bridge_v0",
            extractor=extractor,
            extensions=extensions,
            occupied_cells=occupied,
            output_stub=c1,
            output_dir=CardinalDirection.EAST,
            transport_kind=transport_kind,
            base_throughput=1,
            base_score=1.0,
            route_probe_result=probe,
        )

    left = _bundle("rim_left", frozenset({c0}), stale_ok)
    right = _bundle("rim_right", frozenset({c2}), stale_ok)
    genome = Genome(
        "narrow_bridge_g",
        (Gene("rim_left", True, 0), Gene("rim_right", True, 1)),
        seed=42,
    )
    return (left, right), genome


def build_rim_competition_genome(
    *,
    left_commit_order: int = 0,
    right_commit_order: int = 1,
) -> Genome:
    """Same pool ids as :func:`build_rim_competition_pool`; only ``commit_order`` differs."""

    return Genome(
        "narrow_bridge_g_ordered",
        (
            Gene("rim_left", True, left_commit_order),
            Gene("rim_right", True, right_commit_order),
        ),
        seed=42,
    )
