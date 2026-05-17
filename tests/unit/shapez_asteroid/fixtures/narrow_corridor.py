"""Narrow-corridor optimization fixtures (Sequence 10A).

Geometry: 1-wide bridge cell ``(1, 0)`` between rim extractors at ``(0, 0)`` and ``(2, 0)``.
The bridge may be marked ``protected_corridor_cells`` so the seed ``route_domain`` uses
``RouteClass.NARROW_CORRIDOR`` (see ``RouteDomainSnapshotBuilder``).

**Asymmetric default** (``build_narrow_bridge_optimization_input``): a single ``RouteGoal`` on
``rim_right`` documents rim-right goal bias (Sequence 10A regression).

**Symmetric variant** (``build_symmetric_narrow_bridge_optimization_input``): goals on both
rim cells; each candidate's ``occupied_cells`` overlay blocks its own rim goal cell, so
``run_route_probe`` from the shared bridge stub naturally targets the **opposite** rim.
Commit order then decides which side consumes the bridge first (no rim_right-only goal).

**JSON golden** (``json_safe_replay_value`` export):
``tests/fixtures/shapez_asteroid/optimization/narrow_corridor_{asymmetric,symmetric}_rim_competition.json``;
builder parity: ``test_narrow_corridor_optimization_json_fixtures.py``;
strict ``schema_version`` 1 parse/round-trip (test-only, not production solver input):
``fixtures/optimization_json.py`` + ``test_optimization_fixture_json_contract.py``.

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


def build_symmetric_narrow_bridge_optimization_input(
    *,
    protected_bridge: bool = True,
    existing_trunk_overlap: bool = False,
) -> tuple[OptimizationInput, frozenset[RouteGoal]]:
    """Same three-cell strip as :func:`build_narrow_bridge_optimization_input`, dual rim goals.

    Both ``(0, 0)`` and ``(2, 0)`` are ``RouteGoalKind.EXTERNAL_MARGIN``. During commit, each
    candidate overlays its extractor rim; the opposite rim remains the only reachable goal from
    the shared bridge output stub ``(1, 0)``, so geometry does not hard-code a single-sided goal.
    """

    c0, c1, c2 = narrow_bridge_coords()
    coords = (c0, c1, c2)
    ac = frozenset(coords)
    rim = frozenset({c0, c2})
    mineable = ac
    interior = frozenset({c1})
    ext_void: frozenset[Coord] = frozenset()
    goal_west = RouteGoal(c0, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    goal_east = RouteGoal(c2, RouteGoalKind.EXTERNAL_MARGIN, None, 0, False)
    goals = frozenset({goal_west, goal_east})
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
        route_goals=goals,
        existing_transport_cells=frozenset(),
        existing_trunk_cells=trunk_overlap,
        protected_corridor_cells=protected,
        blocked_cells=frozenset(),
        topology_graph=topo,
        bbox=bbox,
    )
    return inp, goals


def build_symmetric_rim_competition_pool(
    inp: OptimizationInput,
    *,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
) -> tuple[tuple[BundleCandidate, ...], Genome]:
    """Dual goals on both rims; solo probes mirror opposite-rim delivery via the bridge."""

    c0, c1, c2 = narrow_bridge_coords()
    by_x = sorted(inp.route_goals, key=lambda z: (z.coord.x, z.coord.y))
    if len(by_x) != 2:
        raise ValueError("symmetric pool expects exactly two route_goals on the narrow strip")
    goal_west, goal_east = by_x[0], by_x[1]
    if goal_west.coord != c0 or goal_east.coord != c2:
        raise ValueError("symmetric pool expects goals at strip ends (0,0) and (2,0)")

    left_probe = RouteProbeResult(
        reachable=True,
        path=(c1, c2),
        cost=len((c1, c2)),
        expanded_nodes=len((c1, c2)),
        reached_goal=goal_east,
        goal_priority=goal_east.priority,
        failure_reason=None,
    )
    right_probe = RouteProbeResult(
        reachable=True,
        path=(c1, c0),
        cost=len((c1, c0)),
        expanded_nodes=len((c1, c0)),
        reached_goal=goal_west,
        goal_priority=goal_west.priority,
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
            pattern_id="sym_narrow_bridge",
            topology_signature="sym_narrow_bridge_v0",
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

    left = _bundle("sym_rim_left", frozenset({c0}), left_probe)
    right = _bundle("sym_rim_right", frozenset({c2}), right_probe)
    genome = Genome(
        "sym_narrow_bridge_g",
        (Gene("sym_rim_left", True, 0), Gene("sym_rim_right", True, 1)),
        seed=42,
    )
    return (left, right), genome


def build_symmetric_rim_competition_genome(
    *,
    left_commit_order: int = 0,
    right_commit_order: int = 1,
) -> Genome:
    """Same candidate ids as :func:`build_symmetric_rim_competition_pool`; ``commit_order`` only."""

    return Genome(
        "sym_narrow_bridge_g_ordered",
        (
            Gene("sym_rim_left", True, left_commit_order),
            Gene("sym_rim_right", True, right_commit_order),
        ),
        seed=42,
    )
