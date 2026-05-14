"""Telemetry: trunk seed empty-pool diagnostics (Path A post-audit)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_goal_trunk_seed as s4gts,
)


def test_trunk_seed_union_ignores_cleanup_only_hints() -> None:
    ela = {
        "solver_hints": {
            "trunk_seed_cell_union": [],
            "cleanup_candidate_cell_union": [[9, 9]],
        }
    }
    assert s4gts.trunk_seed_union_from_existing_layout(ela) == set()


def test_diagnose_trunk_seed_pool_empty_wrong_kind_on_map() -> None:
    ela = {"solver_hints": {"trunk_seed_cell_union": [[5, 5]]}}
    cells = {
        (5, 5): {"role": "occupied", "layout_kind": "unknown_kind_marker"},
    }
    bad = {"shape_belt": set(), "fluid_pipe": set()}
    assert (
        s4gts.diagnose_trunk_seed_pool_empty(
            existing_layout_analysis=ela,
            cells=cells,
            margin_cells=set(),
            trunk_seed_by_kind=bad,
        )
        == "main_component_wrong_kind"
    )


def test_diagnose_trunk_seed_candidate_zero_wrong_transport_kind() -> None:
    ela = {"solver_hints": {"trunk_seed_cell_union": [[5, 5]]}}
    cells = {(5, 5): {"role": "belt", "layout_kind": None}}
    r = s4gts.diagnose_trunk_seed_candidate_zero_for_kind(
        transport_kind="fluid_pipe",
        existing_layout_analysis=ela,
        cells=cells,
        margin_cells=set(),
        seeds_for_kind=set(),
        existing_reaching=set(),
    )
    assert r == "main_component_wrong_kind"


def test_diagnose_trunk_seed_candidate_zero_not_external_reachable_synthetic() -> None:
    """Synthetic empty ``seeds_for_kind`` with ELA belt + first-route reachability (telemetry)."""

    ela = {"solver_hints": {"trunk_seed_cell_union": [[5, 5]]}}
    cells = {(5, 5): {"role": "belt", "layout_kind": None}}
    r = s4gts.diagnose_trunk_seed_candidate_zero_for_kind(
        transport_kind="shape_belt",
        existing_layout_analysis=ela,
        cells=cells,
        margin_cells=set(),
        seeds_for_kind=set(),
        existing_reaching=set(),
    )
    assert r == "main_component_not_external_reachable"
