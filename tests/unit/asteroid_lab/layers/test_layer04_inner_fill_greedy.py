"""L4-1 greedy inner fill contract tests."""

from __future__ import annotations

from types import MappingProxyType

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import BundleCellRole
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    PATTERN_BUILTIN_1X1_FIELD_BLOCK,
    Layer04SkipReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.placement_state import (
    PlacementCommitState,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
    ProvisionalPlacedCell,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    LAYER_03_GREEDY_SOURCE,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing import (
    route_domain,
    sequential_router,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill import (
    candidate_domain,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)
from shapez2_factory.application.asteroid_lab.layers.observability.post_summary_metrics import (
    build_layer04_inner_fill_post_summary_metrics,
)
from tests.unit.asteroid_lab.layers.fixtures.l5_l4_occupancy_barrier import (
    L5_L4_CHOKE_VOID,
    L5_L4_MINER,
    L5_L4_STUB,
    L5_L4_WEST_VOID,
    l5_l4_occupancy_barrier_basic_map,
    l5_l4_occupancy_barrier_exterior_plan,
    l5_l4_occupancy_barrier_no_detour_map,
    l5_l4_occupancy_barrier_rim_result,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_interior_golden import (
    GOLDEN_5X5_INTERIOR_CANDIDATES,
    GOLDEN_5X5_L3_EQUIPMENT_FOOTPRINT,
    golden_5x5_interior_complete_map,
    golden_5x5_interior_extension_footprint_overlay,
    golden_5x5_interior_full_field_overlay,
    golden_5x5_interior_provisional_overlay,
    golden_5x5_interior_witness_pollution_overlay,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import make_complete_map


def _generous_budget() -> LayerBudgetContext:
    return LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)


def _barrier_l3_overlay_miner_only() -> ProvisionalLayoutOverlay:
    cell = ProvisionalPlacedCell(
        coord=L5_L4_MINER,
        candidate_id="l5_l4_p0",
        placement_id="l5_l4_p0",
        role=BundleCellRole.MINER,
        transport_kind=TransportKind.SHAPE_BELT,
        placement_state=PlacementCommitState.PROVISIONAL_PLACED,
    )
    return ProvisionalLayoutOverlay(
        occupied_cells=frozenset({L5_L4_MINER}),
        extractor_cells=frozenset({L5_L4_MINER}),
        extension_cells=frozenset(),
        transport_stub_cells=frozenset({L5_L4_STUB}),
        by_cell=MappingProxyType({L5_L4_MINER: cell}),
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


def _barrier_case_b_map():
    """Choke coord is field + interior candidate so L4 can block it."""

    base = l5_l4_occupancy_barrier_basic_map()
    field = frozenset({L5_L4_MINER, L5_L4_CHOKE_VOID})
    void = base.external_void_cells - field
    return make_complete_map(field_cells=field, external_void_cells=void)


def _barrier_case_c_map():
    """West + choke are field interior cells; L4 fill blocks all void paths."""

    base = l5_l4_occupancy_barrier_no_detour_map()
    field = frozenset({L5_L4_MINER, L5_L4_CHOKE_VOID, L5_L4_WEST_VOID})
    void = base.external_void_cells - field
    return make_complete_map(field_cells=field, external_void_cells=void)


def test_interior_candidates_count_13_on_golden_fixture() -> None:
    candidates = candidate_domain.compute_interior_candidates(
        complete_map=golden_5x5_interior_complete_map(),
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
    )
    assert len(candidates) == 13
    assert candidates == GOLDEN_5X5_INTERIOR_CANDIDATES


def test_extension_cells_subtracted_from_interior_candidates() -> None:
    complete_map = golden_5x5_interior_complete_map()
    overlay = golden_5x5_interior_extension_footprint_overlay()
    candidates = candidate_domain.compute_interior_candidates(
        complete_map=complete_map,
        provisional_overlay=overlay,
    )
    assert (4, 4) not in candidates
    assert len(candidates) == len(complete_map.field_cells) - 1


def test_l3_witness_stub_not_subtracted_from_candidates() -> None:
    complete_map = golden_5x5_interior_complete_map()
    polluted = golden_5x5_interior_witness_pollution_overlay()
    candidates = candidate_domain.compute_interior_candidates(
        complete_map=complete_map,
        provisional_overlay=polluted,
    )
    assert candidates == GOLDEN_5X5_INTERIOR_CANDIDATES
    assert polluted.occupied_cells != polluted.extractor_cells | polluted.extension_cells


def test_greedy_places_builtin_1x1_field_block() -> None:
    result = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_generous_budget(),
    )
    assert len(result.interior_occupied_cells) >= 1
    assert result.interior_occupied_cells <= GOLDEN_5X5_INTERIOR_CANDIDATES
    assert result.interior_occupied_cells <= golden_5x5_interior_complete_map().field_cells
    assert all(p.pattern_id == PATTERN_BUILTIN_1X1_FIELD_BLOCK for p in result.placements)
    assert result.interior_occupied_cells.isdisjoint(GOLDEN_5X5_L3_EQUIPMENT_FOOTPRINT)
    block_cells = frozenset(p.coord for p in result.placements)
    routeable_cells = frozenset(
        cell
        for group in result.routeable_inner_groups
        for cell in (group.miner_cells | group.extension_cells)
    )
    assert block_cells | routeable_cells == result.interior_occupied_cells


def test_greedy_lexicographic_scan_order() -> None:
    result = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_generous_budget(),
    )
    assert result.placements[0].coord == (2, 2)
    expected_coords = tuple(sorted(GOLDEN_5X5_INTERIOR_CANDIDATES, key=lambda c: (c[0], c[1])))
    assert tuple(p.coord for p in result.placements) == expected_coords


def test_coverage_ratio_denominator() -> None:
    result = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_generous_budget(),
    )
    assert result.metrics is not None
    assert result.metrics.coverage_ratio == len(result.interior_occupied_cells) / 13


def test_no_candidates_skip_reason() -> None:
    result = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_full_field_overlay(),
        budget_ctx=_generous_budget(),
    )
    assert result.skip_reason is Layer04SkipReason.NO_CANDIDATES
    assert result.interior_occupied_cells == frozenset()


def test_budget_exhausted_zero_placements() -> None:
    result = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=LayerBudgetContext(
            deadline_monotonic=0.0,
            started_monotonic=0.0,
            now_fn=lambda: 1.0,
        ),
    )
    assert result.skip_reason is Layer04SkipReason.BUDGET_EXHAUSTED
    assert result.interior_occupied_cells == frozenset()
    assert result.metrics is not None
    assert result.metrics.budget_interrupted is True


def test_budget_partial_fill_valid_result() -> None:
    checks = [0]

    def now_fn() -> float:
        checks[0] += 1
        return 0.0 if checks[0] == 1 else 10.0

    result = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=LayerBudgetContext(
            deadline_monotonic=1.0,
            started_monotonic=0.0,
            now_fn=now_fn,
        ),
    )
    assert result.skip_reason is None
    assert result.metrics is not None
    assert result.metrics.budget_interrupted is True
    assert len(result.interior_occupied_cells) == 1
    assert result.interior_occupied_cells == frozenset({(2, 2)})


def test_corridor_shadow_disjoint_from_interior_occupied() -> None:
    result = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_generous_budget(),
    )
    assert result.corridor_shadow_cells.isdisjoint(result.interior_occupied_cells)


def test_no_void_contamination() -> None:
    complete_map = golden_5x5_interior_complete_map()
    result = run_layer_04_inner_pattern_fill(
        complete_map=complete_map,
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_generous_budget(),
    )
    assert result.interior_occupied_cells.isdisjoint(complete_map.external_void_cells)


def test_l4_fill_excluded_from_l5_walkable_domain() -> None:
    complete_map = golden_5x5_interior_complete_map()
    fill = run_layer_04_inner_pattern_fill(
        complete_map=complete_map,
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_generous_budget(),
    )
    domain = route_domain.build_l4_route_search_domain(
        complete_map=complete_map,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
        interior_occupied_cells=fill.interior_occupied_cells,
    )
    for coord in fill.interior_occupied_cells:
        assert coord not in domain.walkable_cells


def test_l4_to_l5_case_b_reroute_via_fill_interior() -> None:
    complete_map = _barrier_case_b_map()
    overlay = _barrier_l3_overlay_miner_only()
    fill = run_layer_04_inner_pattern_fill(
        complete_map=complete_map,
        exterior_plan=None,
        provisional_overlay=overlay,
        budget_ctx=_generous_budget(),
    )
    assert L5_L4_CHOKE_VOID in fill.interior_occupied_cells

    domain = route_domain.build_l4_route_search_domain(
        complete_map=complete_map,
        miner_cells=frozenset({L5_L4_MINER}),
        extension_cells=frozenset(),
        interior_occupied_cells=fill.interior_occupied_cells,
    )
    assert L5_L4_CHOKE_VOID not in domain.walkable_cells

    blocked = sequential_router.route_layer04_sequential(
        complete_map=complete_map,
        exterior_plan=l5_l4_occupancy_barrier_exterior_plan(),
        rim_result=l5_l4_occupancy_barrier_rim_result(),
        resource_kind="shape",
        interior_occupied_cells=fill.interior_occupied_cells,
    )
    assert len(blocked.routes) == 1
    assert L5_L4_CHOKE_VOID not in blocked.routes[0].path_coords


def test_layer04_post_summary_metrics_from_fill_result() -> None:
    fill = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_generous_budget(),
    )
    metrics = build_layer04_inner_fill_post_summary_metrics(fill)
    assert metrics["stub"] is False
    assert metrics["interior_occupied_cell_count"] == len(fill.interior_occupied_cells)
    assert metrics["coverage_ratio"] == fill.metrics.coverage_ratio
    assert metrics["budget_interrupted"] is False
    assert metrics["layer_skip_reason"] is None


def test_layer04_post_summary_metrics_stub_when_not_fill_result() -> None:
    metrics = build_layer04_inner_fill_post_summary_metrics(None)
    assert metrics["stub"] is True
    assert metrics["interior_occupied_cell_count"] == 0


def test_layer04_post_summary_metrics_partial_fill_budget_interrupted() -> None:
    checks = [0]

    def now_fn() -> float:
        checks[0] += 1
        return 0.0 if checks[0] == 1 else 10.0

    fill = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=LayerBudgetContext(
            deadline_monotonic=1.0,
            started_monotonic=0.0,
            now_fn=now_fn,
        ),
    )
    metrics = build_layer04_inner_fill_post_summary_metrics(fill)
    assert metrics["budget_interrupted"] is True
    assert metrics["layer_skip_reason"] is None
    assert metrics["interior_occupied_cell_count"] == 1


def test_l4_to_l5_case_c_route_not_found_via_fill_interior() -> None:
    complete_map = _barrier_case_c_map()
    overlay = _barrier_l3_overlay_miner_only()
    fill = run_layer_04_inner_pattern_fill(
        complete_map=complete_map,
        exterior_plan=None,
        provisional_overlay=overlay,
        budget_ctx=_generous_budget(),
    )
    assert L5_L4_CHOKE_VOID in fill.interior_occupied_cells
    assert L5_L4_WEST_VOID in fill.interior_occupied_cells

    plan = sequential_router.route_layer04_sequential(
        complete_map=complete_map,
        exterior_plan=l5_l4_occupancy_barrier_exterior_plan(),
        rim_result=l5_l4_occupancy_barrier_rim_result(),
        resource_kind="shape",
        interior_occupied_cells=fill.interior_occupied_cells,
    )
    assert plan.routes == ()
    assert len(plan.failures) == 1
    assert plan.failures[0].reason is Layer04FailureReason.ROUTE_NOT_FOUND
    assert "blocked_by_l4_interior_count=" in plan.failures[0].detail
