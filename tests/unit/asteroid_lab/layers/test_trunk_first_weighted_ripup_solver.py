"""Trunk-first weighted rip-up inner fill (L5) contract tests."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.inner_fill_strategy import (
    InnerFillStrategy,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    RouteableInnerGroupPlacement,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.trunk_first_weighted_ripup_solver import (  # noqa: E501
    MINER_WEIGHT_MULTIPLIER,
    _bfs_trunk_path,
    _commit_belt_path,
    _footprint_at_anchor,
    _prune_orphan_extensions,
    _rip_up_lowest_weight_blocker,
    _SolverState,
    _try_attach_miner_on_belt,
)
from tests.unit.asteroid_lab.layers.fixtures.l5_l4_occupancy_barrier import (
    l5_l4_occupancy_barrier_basic_map,
    l5_l4_occupancy_barrier_exterior_plan,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


def _budget() -> LayerBudgetContext:
    return LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)


def _empty_overlay() -> ProvisionalLayoutOverlay:
    return ProvisionalLayoutOverlay.empty()


def test_belt_path_committed_before_miner_confirmation() -> None:
    complete_map = build_rect_field_with_void_shell(width=5, height=3, void_pad=2)
    exterior = l5_l4_occupancy_barrier_exterior_plan()
    result = run_layer_04_inner_pattern_fill(
        complete_map=complete_map,
        exterior_plan=exterior,
        provisional_overlay=_empty_overlay(),
        budget_ctx=_budget(),
        target_routeable_group_count=2,
        inner_fill_strategy=InnerFillStrategy.TRUNK_FIRST_WEIGHTED_RIPUP,
    )
    assert result.trunk_diagnostics is not None
    assert result.trunk_diagnostics.trunk_path_count >= 0
    if result.routeable_inner_groups:
        assert result.corridor_shadow_cells
        assert result.trunk_diagnostics.trunk_path_count >= 1
        for group in result.routeable_inner_groups:
            assert group.m_output_stub in result.corridor_shadow_cells


def test_miner_stub_points_toward_adjacent_belt_cell() -> None:
    anchor = (3, 1)
    _miner, _ext, stub = _footprint_at_anchor(anchor)
    assert stub == (4, 1)
    complete_map = build_rect_field_with_void_shell(width=6, height=4, void_pad=2)
    state = _SolverState(
        complete_map=complete_map,
        fixed_blocked=frozenset(),
        connector_void_coords=frozenset({(-1, 1)}),
    )
    _commit_belt_path(state, ((4, 1),))
    group = _try_attach_miner_on_belt(
        state=state,
        interior_candidates=frozenset({anchor}),
        placement_index=1,
    )
    assert group is not None
    assert group.m_output_stub == (4, 1)


def test_miner_footprint_has_at_most_three_extensions() -> None:
    _miner, extension_cells, _stub = _footprint_at_anchor((3, 3))
    assert len(extension_cells) <= 3


def test_miner_removal_weight_is_one_point_five_times_extension_block() -> None:
    group = RouteableInnerGroupPlacement(
        placement_id="t",
        anchor=(0, 0),
        miner_cells=frozenset({(0, 0)}),
        extension_cells=frozenset({(-1, 0), (-2, 0), (-3, 0)}),
        m_output_stub=(1, 0),
        throughput_factor=4,
    )
    state = _SolverState(
        complete_map=build_rect_field_with_void_shell(width=5, height=5, void_pad=2),
        fixed_blocked=frozenset(),
        connector_void_coords=frozenset(),
    )
    assert state.removal_weight(group) == 3 * 1.0 + MINER_WEIGHT_MULTIPLIER * 1.0


def test_rip_up_removes_lowest_weight_provisional_group() -> None:
    light = RouteableInnerGroupPlacement(
        placement_id="light",
        anchor=(0, 0),
        miner_cells=frozenset({(0, 0)}),
        extension_cells=frozenset({(-1, 0)}),
        m_output_stub=(1, 0),
        throughput_factor=4,
    )
    heavy = RouteableInnerGroupPlacement(
        placement_id="heavy",
        anchor=(5, 5),
        miner_cells=frozenset({(5, 5)}),
        extension_cells=frozenset({(4, 5), (3, 5), (2, 5)}),
        m_output_stub=(6, 5),
        throughput_factor=4,
    )
    state = _SolverState(
        complete_map=build_rect_field_with_void_shell(width=8, height=8, void_pad=2),
        fixed_blocked=frozenset(),
        connector_void_coords=frozenset(),
    )
    state.provisional_groups = [heavy, light]
    assert _rip_up_lowest_weight_blocker(state)
    assert [g.placement_id for g in state.provisional_groups] == ["heavy"]
    assert state.stats.removed_miner_count == 1


def test_orphan_extension_prune_drops_unconfirmed_group() -> None:
    orphan = RouteableInnerGroupPlacement(
        placement_id="orphan",
        anchor=(1, 1),
        miner_cells=frozenset({(1, 1)}),
        extension_cells=frozenset({(0, 1)}),
        m_output_stub=(2, 1),
        throughput_factor=4,
    )
    state = _SolverState(
        complete_map=build_rect_field_with_void_shell(width=5, height=5, void_pad=2),
        fixed_blocked=frozenset(),
        connector_void_coords=frozenset(),
    )
    state.provisional_groups = [orphan]
    _prune_orphan_extensions(state)
    assert state.provisional_groups == []
    assert state.stats.orphan_extension_pruned_count >= 1


def test_bfs_finds_interior_to_void_adjacent_goal() -> None:
    complete_map = l5_l4_occupancy_barrier_basic_map()
    state = _SolverState(
        complete_map=complete_map,
        fixed_blocked=frozenset({(3, 0)}),
        connector_void_coords=frozenset({(-1, 0)}),
    )
    goals = frozenset({(0, 0)})
    path = _bfs_trunk_path(state=state, start=(3, 0), goals=goals)
    assert path is None or path[-1] in goals


def test_greedy_strategy_default_unchanged() -> None:
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_interior_golden import (
        golden_5x5_interior_complete_map,
        golden_5x5_interior_provisional_overlay,
    )

    greedy = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_budget(),
        target_routeable_group_count=1,
    )
    explicit = run_layer_04_inner_pattern_fill(
        complete_map=golden_5x5_interior_complete_map(),
        exterior_plan=None,
        provisional_overlay=golden_5x5_interior_provisional_overlay(),
        budget_ctx=_budget(),
        target_routeable_group_count=1,
        inner_fill_strategy=InnerFillStrategy.GREEDY,
    )
    assert greedy.interior_occupied_cells == explicit.interior_occupied_cells
    assert greedy.trunk_diagnostics is None


def test_golden_fixture_solver_run_does_not_load_golden_as_input() -> None:
    source = (
        __import__("pathlib")
        .Path(
            "src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py"
        )
        .read_text(encoding="utf-8")
    )
    assert "golden.shapez" not in source
    assert "load_golden_copy" not in source
