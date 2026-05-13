"""``fluid_pipe`` STEP4 exterior margin goal reload when committed trunk is BFS-unreachable."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_goal_trunk_seed as _s4gts,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_search_diagnostics as _s4sd_diag,
)


def test_fluid_committed_primary_goal_set_omits_margin_until_reload() -> None:
    """Primary raw = committed only → ``goal_primary`` excludes margin unless on live trunk."""

    margin = {(1, 0), (2, 0)}
    committed = {"fluid_pipe": {(5, 0), (6, 0)}}
    seeds = {"shape_belt": set(), "fluid_pipe": {(9, 9)}}
    raw_full = _s4gts.build_step4_goal_set(
        "fluid_pipe",
        committed_trunk_by_kind=committed,
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=seeds,
    )
    assert margin <= raw_full
    goal_full, _ = _s4sd_diag.merge_goal_union_meta(
        (4, 0),
        raw_goal=set(raw_full),
        trunk_cells=frozenset({(7, 0)}),
        margin_cells=margin,
    )
    goal_primary, _ = _s4sd_diag.merge_goal_union_meta(
        (4, 0),
        raw_goal=set(committed["fluid_pipe"]),
        trunk_cells=frozenset({(7, 0)}),
        margin_cells=margin,
    )
    margin_only = frozenset(margin) - goal_primary
    assert margin_only == frozenset(margin)
    assert len(goal_primary) < len(goal_full)


def test_fluid_no_mixed_transport_goal_set_with_shape_committed() -> None:
    """Committed shape belt must not appear in ``fluid_pipe`` raw goals."""

    margin = {(1, 1)}
    committed = {"shape_belt": {(5, 5)}}
    seeds: dict[str, set[Coord]] = {"shape_belt": {(5, 5)}, "fluid_pipe": {(6, 6)}}
    g_fluid = _s4gts.build_step4_goal_set(
        "fluid_pipe",
        committed_trunk_by_kind=committed,
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=seeds,
    )
    assert (5, 5) not in g_fluid


@pytest.mark.parametrize(
    ("committed", "trunk", "margin", "expect_nonempty_margin_only"),
    [
        ({(5, 0)}, frozenset({(5, 0)}), {(5, 0)}, False),
        ({(5, 0)}, frozenset({(7, 0)}), {(1, 0), (2, 0)}, True),
    ],
)
def test_margin_only_delta_for_primary_union(
    committed: set[Coord],
    trunk: frozenset[Coord],
    margin: set[Coord],
    expect_nonempty_margin_only: bool,
) -> None:
    stub: Coord = (4, 0)
    goal_primary, _ = _s4sd_diag.merge_goal_union_meta(
        stub,
        raw_goal=set(committed),
        trunk_cells=trunk,
        margin_cells=margin,
    )
    margin_only = frozenset(margin) - goal_primary
    assert bool(margin_only) is expect_nonempty_margin_only
