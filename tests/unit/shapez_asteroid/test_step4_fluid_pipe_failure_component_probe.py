"""``step4_fluid_pipe_failure_component_probe`` — STEP4 permission BFS, debug-only."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_fluid_pipe_failure_component_probe as fp_probe_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_diagnostic as s4diag_mod,
)


def _open_cell(x: int, y: int) -> dict[str, Any]:
    return {"x": x, "y": y, "role": "occupied", "layout_kind": "asteroid_field"}


def test_probe_returns_none_for_shape_belt() -> None:
    out = fp_probe_mod.build_step4_fluid_pipe_failure_component_probe(
        stub_cell=(2, 2),
        want_role="belt",
        goal_cells=frozenset(),
        trunk_cells=frozenset(),
        trunk_seed_candidates_by_kind={"shape_belt": set(), "fluid_pipe": set()},
        margin_cells=set(),
        blocked=frozenset(),
        hard_extras=frozenset(),
        cells={(2, 2): {"x": 2, "y": 2, "role": "belt"}},
        mineable=frozenset(),
        asteroid=frozenset({(3, 2)}),
        is_external=lambda c: False,
        cheap_reuse_cells=None,
        transport_kind="shape_belt",
    )
    assert out is None


def test_probe_bfs_reachability_and_nearest_unreachable_goal() -> None:
    """Stub reaches (2,2)-(4,2); goal at (6,2) separated by blocked column at x=5."""

    stub: Coord = (2, 2)
    cells: dict[Coord, dict[str, Any]] = {
        stub: {"x": 2, "y": 2, "role": "pipe"},
        (3, 2): _open_cell(3, 2),
        (4, 2): _open_cell(4, 2),
        (6, 2): _open_cell(6, 2),
    }
    for x in range(0, 9):
        for y in range(0, 9):
            if (x, y) in cells:
                continue
            if y == 2 and 2 <= x <= 4:
                continue
            if (x, y) == (5, 2):
                continue
            cells[(x, y)] = {"x": x, "y": y, "role": "belt"}
    blocked = frozenset({(5, 2)})
    goal_cells = frozenset({(6, 2), (3, 2)})
    trunk_cells = frozenset({(3, 2)})
    margin_cells: set[Coord] = {(6, 2)}
    seed = {(99, 99)}
    probe = fp_probe_mod.build_step4_fluid_pipe_failure_component_probe(
        stub_cell=stub,
        want_role="pipe",
        goal_cells=goal_cells,
        trunk_cells=trunk_cells,
        trunk_seed_candidates_by_kind={"fluid_pipe": seed},
        margin_cells=margin_cells,
        blocked=blocked,
        hard_extras=frozenset(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda c: c[0] < 0,
        cheap_reuse_cells=None,
        transport_kind="fluid_pipe",
    )
    assert probe is not None
    assert probe["stub_reachable_cell_count"] == 3
    assert probe["nearest_unreachable_goal_cell"] == [6, 2]
    assert probe["nearest_unreachable_goal_manhattan"] == 4
    assert probe["goal_source_counts"] == {
        "existing_trunk": 1,
        "exterior_margin": 1,
        "trunk_seed": 0,
    }
    assert probe["reachable_goal_source_counts"] == {
        "existing_trunk": 1,
        "exterior_margin": 0,
        "trunk_seed": 0,
    }
    br = probe["blocked_reason_counts_near_frontier"]
    assert br.get("blocked", 0) >= 1
    sample = probe["reachable_frontier_boundary_sample"]
    assert isinstance(sample, list)
    assert len(sample) >= 1


def test_build_step4_route_failure_diagnostic_attaches_probe_for_fluid_pipe_only() -> None:
    detail: dict[str, Any] = {
        "nearest_existing_transport_distance": 1,
        "blocked_reason_near_stub": [],
        "last_error": "no_route_exhausted",
    }
    common = dict(
        rec=None,
        extractor_cell=(1, 2),
        stub_cell=(2, 2),
        want_role="pipe",
        raw_goal={(3, 2)},
        goal_cells=frozenset({(3, 2)}),
        trunk_cells=frozenset(),
        trunk_seed_candidates_by_kind={"fluid_pipe": {(3, 2)}, "shape_belt": set()},
        margin_cells=set(),
        committed_trunk_for_kind=set(),
        blocked=frozenset(),
        hard_extras=frozenset(),
        cells={(2, 2): {"x": 2, "y": 2, "role": "pipe"}, (3, 2): _open_cell(3, 2)},
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda c: False,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "search_mode": "goal_cells_union_legacy"},
        detail=detail,
        final_state=None,
    )
    d_pipe = s4diag_mod.build_step4_route_failure_diagnostic(transport_kind="fluid_pipe", **common)
    assert "step4_fluid_pipe_failure_component_probe" in d_pipe
    p = d_pipe["step4_fluid_pipe_failure_component_probe"]
    assert isinstance(p, dict)
    assert "stub_reachable_cell_count" in p

    d_belt = s4diag_mod.build_step4_route_failure_diagnostic(
        transport_kind="shape_belt",
        **{**common, "want_role": "belt", "cells": {(2, 2): {"x": 2, "y": 2, "role": "belt"}}},
    )
    assert "step4_fluid_pipe_failure_component_probe" not in d_belt
