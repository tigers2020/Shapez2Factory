"""Acceptance locks for the Layer 3 boundary-M repack greedy (m3e_01) contract.

Behavior contract (PR-B):
1. M extractor AND E extensions never sit in exterior void (equipment ⊆ field).
2. Miner anchor is an outer-rim field cell adjacent to external void.
2-1. m3e_01 bundle footprint reaches up to 4 field cells inward (miner + 3 ext).
3. belt/pipe (output stub + route) may be installed in external void.
4. route probe must not reject solely for "no preinstalled belt".
5. route may cross field but at higher cost than void; equipment is a hard blocker.
6. committed placements appear in overlay / metrics / summary.
7. algorithm runs in Layer 3; Layer 4 stays disabled.

Tests that exercise the m3e_01 (miner + up to 3 extensions) layout are RED until
``layout_seed_at_anchor`` accepts ``extension_count`` and the greedy seed catalog
includes m3e_01. Locking tests for the existing contract (route cost, L4 disabled,
runs-in-L3) are green now.
"""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.dps_policy import (
    build_greedy_route_domain,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_seed import (
    GreedyMinerSeed,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.seed_orient import (
    SeedLayout,
    layout_seed_at_anchor,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord, bbox_from_coords
from tests.unit.asteroid_lab.layers.fixtures.layer_03_deep_rim_map import (
    deep_rim_complete_map,
    deep_rim_exterior_plan,
    shallow2_rim_complete_map,
    shallow2_rim_exterior_plan,
)

M3E_SEED = GreedyMinerSeed("m3e_01", intrinsic_priority_rank=1, miner_count=1, extension_count=3)
M1E_SEED = GreedyMinerSeed("rim_greedy_m1e1", intrinsic_priority_rank=1, miner_count=1)


def _budget() -> LayerBudgetContext:
    return LayerBudgetContext.from_budget_ms(60_000)


def _north_rim_column_map(*, depth: int, anchor_x: int = 2) -> ReconstructionCompleteMap:
    """Single inward column from north-rim anchor ``(anchor_x, 0)`` with stub void above.

    North decreases ``y`` (``cardinal_map``): anchor at y=0, stub void at y=-1,
    extensions extend inward (south) at y=1..depth-1.
    """
    field = frozenset((anchor_x, y) for y in range(depth))
    void = frozenset({(anchor_x, -1)})
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=depth,
        fluid_field_cell_count=0,
        external_void_cells=void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def _layout_m3e(complete_map: ReconstructionCompleteMap, *, anchor: Coord) -> object:
    return layout_seed_at_anchor(
        seed_id="m3e_01",
        anchor=anchor,
        output_dir="N",
        complete_map=complete_map,
        extension_count=3,
    )


# --- Criterion 2-1 / 1 / 3: m3e_01 inward layout (RED until layout supports extension_count) ---


def test_m3e_layout_places_three_extensions_inward() -> None:
    cmap = _north_rim_column_map(depth=4)
    layout = _layout_m3e(cmap, anchor=(2, 0))
    assert isinstance(layout, SeedLayout)
    assert layout.miner_cells == frozenset({(2, 0)})
    assert layout.extension_cells == frozenset({(2, 1), (2, 2), (2, 3)})


def test_m3e_extensions_and_miner_stay_in_field() -> None:
    cmap = _north_rim_column_map(depth=4)
    layout = _layout_m3e(cmap, anchor=(2, 0))
    assert isinstance(layout, SeedLayout)
    assert layout.equipment_cells <= cmap.field_cells


def test_m3e_output_stub_is_external_void() -> None:
    cmap = _north_rim_column_map(depth=4)
    layout = _layout_m3e(cmap, anchor=(2, 0))
    assert isinstance(layout, SeedLayout)
    assert layout.m_output_stub == (2, -1)
    assert layout.m_output_stub in cmap.external_void_cells
    assert layout.m_output_stub not in cmap.field_cells


def test_m3e_footprint_depth_at_most_four() -> None:
    cmap = _north_rim_column_map(depth=4)
    layout = _layout_m3e(cmap, anchor=(2, 0))
    assert isinstance(layout, SeedLayout)
    # miner + up to 3 extensions == at most 4 field cells deep.
    assert len(layout.equipment_cells) <= 4
    inward_depth = max(abs(c[1] - 0) for c in layout.equipment_cells)
    assert inward_depth <= 3


# --- Extension truncation (degrade) ---


def test_m3e_degrades_to_two_extensions_when_inward_field_is_short() -> None:
    cmap = _north_rim_column_map(depth=3)  # miner + only 2 inward field cells
    layout = _layout_m3e(cmap, anchor=(2, 0))
    assert isinstance(layout, SeedLayout)
    assert layout.extension_cells == frozenset({(2, 1), (2, 2)})
    assert len(layout.extension_cells) == 2


def test_m3e_degrades_to_one_extension_when_inward_field_is_short() -> None:
    cmap = _north_rim_column_map(depth=2)  # miner + only 1 inward field cell
    layout = _layout_m3e(cmap, anchor=(2, 0))
    assert isinstance(layout, SeedLayout)
    assert layout.extension_cells == frozenset({(2, 1)})
    assert len(layout.extension_cells) == 1


# --- Run-level integration (RED until greedy passes extension_count through) ---


def test_run_commits_m3e_bundle_with_three_extensions() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=deep_rim_complete_map(),
        exterior_plan=deep_rim_exterior_plan(),
        budget_ctx=_budget(),
        seed_catalog=(M3E_SEED,),
    )
    assert result.metrics.committed_placement_count >= 1
    assert any(len(p.extension_cells) == 3 for p in result.committed_placements)
    # criterion 1: all committed equipment stays on field, all stubs in void.
    field = deep_rim_complete_map().field_cells
    void = deep_rim_complete_map().external_void_cells
    for placement in result.committed_placements:
        assert placement.miner_cells <= field
        assert placement.extension_cells <= field
        assert placement.m_output_stub in void


def test_committed_placements_appear_in_overlay_and_metrics() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=deep_rim_complete_map(),
        exterior_plan=deep_rim_exterior_plan(),
        budget_ctx=_budget(),
        seed_catalog=(M3E_SEED,),
    )
    committed = result.committed_placements
    assert committed
    overlay = result.provisional_overlay
    for placement in committed:
        for cell in placement.miner_cells | placement.extension_cells:
            assert cell in overlay.occupied_cells
    assert result.pass2_report.extension_count == sum(len(p.extension_cells) for p in committed)
    assert result.metrics.committed_placement_count == len(committed)


def test_route_probe_succeeds_without_preinstalled_transport() -> None:
    # No belt/pipe is pre-placed anywhere; routing must still succeed (criterion 4).
    result = run_layer_03_rim_greedy_placement(
        complete_map=deep_rim_complete_map(),
        exterior_plan=deep_rim_exterior_plan(),
        budget_ctx=_budget(),
        seed_catalog=(M3E_SEED,),
    )
    assert result.committed_placements
    assert all(len(p.route_probe_path) >= 1 for p in result.committed_placements)


def test_committed_placement_records_actual_extension_count_after_degrade() -> None:
    # Shallow field: north/south rim anchors fit only 2 inward extensions.
    result = run_layer_03_rim_greedy_placement(
        complete_map=shallow2_rim_complete_map(),
        exterior_plan=shallow2_rim_exterior_plan(),
        budget_ctx=_budget(),
        seed_catalog=(M3E_SEED,),
    )
    assert result.committed_placements
    assert any(len(p.extension_cells) == 2 for p in result.committed_placements)


def test_greedy_prefers_larger_bundle_to_maximize_yield() -> None:
    # Given both m3e_01 (3 ext) and m1e1 (1 ext), greedy commits the larger bundle.
    result = run_layer_03_rim_greedy_placement(
        complete_map=deep_rim_complete_map(),
        exterior_plan=deep_rim_exterior_plan(),
        budget_ctx=_budget(),
        seed_catalog=(M3E_SEED, M1E_SEED),
    )
    assert any(len(p.extension_cells) == 3 for p in result.committed_placements)


def test_default_seed_catalog_is_m3e_01_with_three_extensions() -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_seed import (
        DEFAULT_GREEDY_SEEDS,
    )

    assert any(s.seed_id == "m3e_01" and s.extension_count == 3 for s in DEFAULT_GREEDY_SEEDS)


# --- Criterion 5: field route allowed but costed; equipment is a hard blocker (green) ---


def test_field_route_is_allowed_but_costed_higher_than_void() -> None:
    cmap = deep_rim_complete_map()
    bbox = bbox_from_coords(cmap.field_cells | cmap.external_void_cells)
    field_cell = next(iter(cmap.field_cells))
    void_cell = next(iter(cmap.external_void_cells))
    domain = build_greedy_route_domain(
        complete_map=cmap,
        search_bbox=bbox,
        occupied_equipment_cells=frozenset({field_cell}),
    )
    # field is walkable but more expensive than void (lower routing priority).
    other_field = next(c for c in cmap.field_cells if c != field_cell)
    assert domain.step_cost(other_field) is not None
    assert domain.step_cost(void_cell) is not None
    assert domain.step_cost(other_field) > domain.step_cost(void_cell)
    # committed equipment cell is a hard blocker.
    assert domain.step_cost(field_cell) is None


# --- Criterion 7: runs in Layer 3; Layer 4 disabled (green) ---


def test_algorithm_runs_in_layer_3() -> None:
    from django_apps.asteroid_lab.layers.stack_runner import _DEFAULT_RUNNERS, _LAYER_INDEX

    slugs = [r.slug for r in _DEFAULT_RUNNERS]
    assert LAYER_03_RIM_GREEDY_PLACEMENT in slugs
    assert LAYER_04_RIM_BUNDLE_PLACEMENT not in slugs
    assert _LAYER_INDEX[LAYER_03_RIM_GREEDY_PLACEMENT] == 3
    l3_runner = next(r for r in _DEFAULT_RUNNERS if r.slug == LAYER_03_RIM_GREEDY_PLACEMENT)
    assert l3_runner.run is run_layer_03_rim_greedy_placement


def test_layer4_remains_disabled() -> None:
    from django_apps.asteroid_lab.layers.contracts.layer04_disabled import Layer04DisabledResult
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )

    with pytest.warns(DeprecationWarning):
        result = run_layer_04_rim_bundle_placement()
    assert result == Layer04DisabledResult.superseded()
