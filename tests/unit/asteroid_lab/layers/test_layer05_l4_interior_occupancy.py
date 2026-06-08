"""PR-L5-P0: L4 interior_occupied_cells hard-block in L5 route domain + commit validator."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing import (
    commit_validator,
    route_domain,
    run,
    sequential_router,
)
from tests.unit.asteroid_lab.layers.fixtures.l5_l4_occupancy_barrier import (
    L5_L4_CHOKE_VOID,
    L5_L4_CONNECTOR,
    L5_L4_MINER,
    L5_L4_STUB,
    L5_L4_WEST_VOID,
    l5_l4_occupancy_barrier_basic_map,
    l5_l4_occupancy_barrier_exterior_plan,
    l5_l4_occupancy_barrier_no_detour_map,
    l5_l4_occupancy_barrier_rim_result,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


def test_l5_blocks_l4_interior_occupied_cell() -> None:
    interior = frozenset({(4, 2)})
    validator = commit_validator.L4CommitValidator(
        equipment_cells=frozenset({(2, 2)}),
        connector_cells=frozenset({(5, 2)}),
        stub_cells=frozenset({(3, 2)}),
        interior_occupied_cells=interior,
    )
    assert validator.validate_route_cell((4, 2)) is Layer04FailureReason.INTERIOR_OCCUPIED_BLOCKED


def test_l5_reroutes_around_l4_interior_occupied_cell() -> None:
    exterior = l5_l4_occupancy_barrier_exterior_plan()
    rim = l5_l4_occupancy_barrier_rim_result()

    baseline = sequential_router.route_layer04_sequential(
        complete_map=l5_l4_occupancy_barrier_no_detour_map(),
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
        interior_occupied_cells=frozenset(),
    )
    blocked_choke = sequential_router.route_layer04_sequential(
        complete_map=l5_l4_occupancy_barrier_basic_map(),
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
        interior_occupied_cells=frozenset({L5_L4_CHOKE_VOID}),
    )

    assert len(baseline.routes) == 1
    assert len(blocked_choke.routes) == 1
    assert L5_L4_CHOKE_VOID in baseline.routes[0].path_coords
    assert L5_L4_CHOKE_VOID not in blocked_choke.routes[0].path_coords


def test_l5_route_not_found_when_l4_blocks_all_paths() -> None:
    complete_map = l5_l4_occupancy_barrier_no_detour_map()
    exterior = l5_l4_occupancy_barrier_exterior_plan()
    rim = l5_l4_occupancy_barrier_rim_result()
    interior = frozenset({L5_L4_CHOKE_VOID, L5_L4_WEST_VOID})

    plan = sequential_router.route_layer04_sequential(
        complete_map=complete_map,
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
        interior_occupied_cells=interior,
    )

    assert plan.routes == ()
    assert len(plan.failures) == 1
    failure = plan.failures[0]
    assert failure.reason is Layer04FailureReason.ROUTE_NOT_FOUND
    assert "blocked_by_l4_interior_count=" in failure.detail


def test_l5_allows_trunk_attach_whitelist_over_interior_block() -> None:
    trunk = L5_L4_CHOKE_VOID
    validator = commit_validator.L4CommitValidator(
        equipment_cells=frozenset({L5_L4_MINER}),
        connector_cells=frozenset({L5_L4_CONNECTOR}),
        stub_cells=frozenset({L5_L4_STUB}),
        interior_occupied_cells=frozenset({trunk}),
        trunk_attach_cells=frozenset({trunk}),
    )
    assert validator.validate_route_cell(trunk) is None


def test_l5_allows_source_stub_and_connector_whitelist() -> None:
    validator = commit_validator.L4CommitValidator(
        equipment_cells=frozenset({L5_L4_MINER}),
        connector_cells=frozenset({L5_L4_CONNECTOR}),
        stub_cells=frozenset({L5_L4_STUB}),
        interior_occupied_cells=frozenset({L5_L4_CHOKE_VOID}),
    )
    assert validator.validate_route_cell(L5_L4_STUB) is None
    assert validator.validate_route_cell(L5_L4_CONNECTOR) is None


def test_l5_interior_block_excluded_from_walkable_domain() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    interior = frozenset({(1, 1)})
    domain = route_domain.build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
        interior_occupied_cells=interior,
    )
    assert (1, 1) not in domain.walkable_cells


def test_run_layer_05_wires_interior_occupied_cells() -> None:
    complete_map = l5_l4_occupancy_barrier_basic_map()
    exterior = l5_l4_occupancy_barrier_exterior_plan()
    rim = l5_l4_occupancy_barrier_rim_result()

    via_runner = run.run_layer_05_transport_routing(
        complete_map=complete_map,
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
        interior_occupied_cells=frozenset({L5_L4_CHOKE_VOID}),
    )
    assert len(via_runner.routes) == 1
    assert L5_L4_CHOKE_VOID not in via_runner.routes[0].path_coords
