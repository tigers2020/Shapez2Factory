"""L3 routing surface reaches exterior-lane L2 connector goals."""

from __future__ import annotations

from decimal import Decimal

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedEntry,
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import RimGreedyPolicy
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    EXTERIOR_LANE_OFFSET,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.candidate_gen import (
    generate_candidates,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.layers.shared.exterior_routing_surface import (
    build_layer03_routing_walkable,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import make_complete_map
from tests.unit.asteroid_lab.layers.helpers.l02_rules import snapshot_rules_for_test


def _symmetric_field_map(*, half_extent: int) -> object:
    field = frozenset(
        (x, y)
        for x in range(-half_extent, half_extent + 1)
        for y in range(-half_extent, half_extent + 1)
    )
    return make_complete_map(field_cells=field, external_void_cells=frozenset())


def _symmetric_field_with_void_shell(*, half_extent: int, void_depth: int) -> object:
    field = frozenset(
        (x, y)
        for x in range(-half_extent, half_extent + 1)
        for y in range(-half_extent, half_extent + 1)
    )
    void: set[Coord] = set()
    frontier: set[Coord] = set()
    for x, y in field:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (x + dx, y + dy)
            if neighbor not in field:
                void.add(neighbor)
                frontier.add(neighbor)
    for _depth in range(void_depth - 1):
        next_frontier: set[Coord] = set()
        for cx, cy in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (cx + dx, cy + dy)
                if neighbor not in field and neighbor not in void:
                    void.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
    return make_complete_map(field_cells=field, external_void_cells=frozenset(void))


def _minimal_seed_catalog() -> GeneticSampleSeedSnapshot:
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(
            GeneticSampleSeedEntry(
                gene_id="m0e",
                resource_kind="both",
                canonical_output_dir="E",
                occupied_offsets=((0, 0),),
                extractor_offset=(0, 0),
                extension_offsets=(),
                output_stub_offset=(1, 0),
                route_probe_start_offset=(2, 0),
                throughput_factor=4,
                topology_signature_base="m0e_base",
            ),
        ),
    )


def test_routing_walkable_includes_east_lane_connector_coord() -> None:
    complete_map = _symmetric_field_map(half_extent=13)
    plan = build_exterior_connection_plan(
        complete_map=complete_map,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        rules=snapshot_rules_for_test(),
        allowed_connector_edges=frozenset({CardinalEdge.EAST}),
    )
    east_goal = next(
        connector.void_coord
        for connector in plan.planned_connectors
        if connector.edge is CardinalEdge.EAST
    )
    max_x = max(coord[0] for coord in complete_map.field_cells)
    max_y = max(coord[1] for coord in complete_map.field_cells)
    assert east_goal == (max_x + EXTERIOR_LANE_OFFSET, max_y + EXTERIOR_LANE_OFFSET)

    walkable, bbox = build_layer03_routing_walkable(
        field_cells=complete_map.field_cells,
        external_void_cells=complete_map.external_void_cells,
        exterior_plan=plan,
    )
    assert east_goal in walkable
    assert bbox.max_x >= east_goal[0]
    assert bbox.max_y >= east_goal[1]


def test_routing_extension_uses_strips_not_full_bbox_area() -> None:
    complete_map = _symmetric_field_with_void_shell(half_extent=13, void_depth=12)
    plan = build_exterior_connection_plan(
        complete_map=complete_map,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        rules=snapshot_rules_for_test(),
    )
    base = complete_map.field_cells | complete_map.external_void_cells
    walkable, bbox = build_layer03_routing_walkable(
        field_cells=complete_map.field_cells,
        external_void_cells=complete_map.external_void_cells,
        exterior_plan=plan,
    )
    extension = walkable - base
    bbox_area_non_field = (
        (bbox.max_x - bbox.min_x + 1) * (bbox.max_y - bbox.min_y + 1) - len(complete_map.field_cells)
    )
    assert len(extension) < bbox_area_non_field // 2
    assert len(extension) < 1500


def test_layer03_finds_route_feasible_candidates_on_exterior_lane_plan() -> None:
    complete_map = _symmetric_field_with_void_shell(half_extent=13, void_depth=12)
    plan = build_exterior_connection_plan(
        complete_map=complete_map,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        rules=snapshot_rules_for_test(),
    )
    candidates = generate_candidates(
        complete_map=complete_map,
        exterior_plan=plan,
        genetic_sample_seeds=_minimal_seed_catalog(),
    )
    assert candidates.metrics.route_feasible_rim_anchor_count > 0
    assert candidates.normal_candidates

    result = run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=plan,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=_minimal_seed_catalog(),
        policy=RimGreedyPolicy.default(),
    )
    assert result.metrics.layer_skip_reason is None
    assert result.metrics.route_feasible_rim_anchor_count > 0
    assert len(result.committed_placements) > 0
