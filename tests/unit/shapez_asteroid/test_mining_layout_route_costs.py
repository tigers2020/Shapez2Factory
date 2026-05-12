"""Mining layout: Pass3 vs repair cost layers and Pass3 commit paths."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INF_COST,
    MINEABLE_ROUTE_COST,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
    MAX_ROUTE_LENGTH_RATIO,
    mining_priority_route_cell_cost,
    reconstruct_mining_priority_transport,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.cost_grid import (
    repair_cell_cost,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.weighted_routing import (
    find_min_demolition_path,
)


def test_mining_priority_route_cell_cost_outside_and_mineable() -> None:
    asteroid = {(x, y) for x in range(5) for y in range(5)}
    mineable = set(asteroid)
    boundary = cells_touching_void(asteroid)
    fixed = frozenset({(10, 10)})
    route_tree: set[tuple[int, int]] = {(20, 0)}
    opp: dict[tuple[int, int], int] = {}
    interior = (2, 2)
    assert interior not in boundary

    assert (
        mining_priority_route_cell_cost(
            (-1, 0),
            asteroid_cells=asteroid,
            mineable_cells=mineable,
            boundary_cells=boundary,
            buildings={},
            fixed_stubs=fixed,
            route_tree=route_tree,
            opportunity_score=opp,
        )
        == 1
    )
    assert (
        mining_priority_route_cell_cost(
            interior,
            asteroid_cells=asteroid,
            mineable_cells=mineable,
            boundary_cells=boundary,
            buildings={},
            fixed_stubs=fixed,
            route_tree=route_tree,
            opportunity_score=opp,
        )
        == 150
    )


def test_mining_priority_route_cell_cost_blocks_building() -> None:
    asteroid = {(0, 0)}
    mineable = set(asteroid)
    boundary = cells_touching_void(asteroid)
    fixed: frozenset[tuple[int, int]] = frozenset()
    route_tree: set[tuple[int, int]] = {(5, 0)}
    assert (
        mining_priority_route_cell_cost(
            (0, 0),
            asteroid_cells=asteroid,
            mineable_cells=mineable,
            boundary_cells=boundary,
            buildings={(0, 0): "extractor"},
            fixed_stubs=fixed,
            route_tree=route_tree,
            opportunity_score={},
        )
        >= 1_000_000_000
    )


def test_repair_cell_cost_is_separate_stack_from_pass3() -> None:
    """Repair stack defaults to INF on rock without allow_mineable_route."""

    asteroid = {(0, 0)}
    cc = repair_cell_cost(
        (0, 0),
        asteroid_cells=asteroid,
        buildings={},
        transport_cells=frozenset(),
    )
    assert cc.cost == INF_COST


def test_repair_cell_cost_mineable_step_override() -> None:
    asteroid = {(1, 0)}
    cc_default = repair_cell_cost(
        (1, 0),
        asteroid_cells=asteroid,
        buildings={},
        transport_cells=frozenset(),
        allow_mineable_route=True,
    )
    assert cc_default.cost == MINEABLE_ROUTE_COST
    cc_high = repair_cell_cost(
        (1, 0),
        asteroid_cells=asteroid,
        buildings={},
        transport_cells=frozenset(),
        allow_mineable_route=True,
        mineable_route_step_cost=120,
    )
    assert cc_high.cost == 120


def test_find_min_demolition_path_mineable_second_phase_toy() -> None:
    """Tight search box so only route crosses one rock cell; mineable+override unlocks it."""

    start = (0, 0)
    goal = (2, 0)
    asteroid = {(1, 0)}
    transport = frozenset({goal})
    locked = frozenset({goal})
    assert (
        find_min_demolition_path(
            start,
            {goal},
            asteroid_cells=asteroid,
            buildings={},
            transport_cells=transport,
            locked_cells=locked,
            search_margin=0,
        )
        is None
    )
    rp = find_min_demolition_path(
        start,
        {goal},
        asteroid_cells=asteroid,
        buildings={},
        transport_cells=transport,
        locked_cells=locked,
        search_margin=0,
        allow_mineable_route=True,
        mineable_route_step_cost=120,
    )
    assert rp is not None
    assert (1, 0) in rp.path
    assert rp.total_cost == 120


def test_pass3_metrics_include_commit_reason_and_capacity_placeholders() -> None:
    """Spine + detachable branch: connectivity uses cardinal pipe adjacency only (P3-B)."""

    asteroid_cells = {(x, y) for x in range(1, 14) for y in range(5)}
    mineable_cells = set(asteroid_cells)
    fixed_stub = (1, 2)
    anchor = (10, 2)
    original_transport = {fixed_stub: "pipe", anchor: "pipe"}
    for x in range(2, 10):
        original_transport[(x, 2)] = "pipe"
    for x in (5, 6, 7):
        original_transport[(x, 1)] = "pipe"
    result = reconstruct_mining_priority_transport(
        anchor=anchor,
        asteroid_cells=asteroid_cells,
        mineable_cells=mineable_cells,
        buildings={},
        transport_cells=original_transport,
        outlets_order=[fixed_stub],
        transport_role="pipe",
    )
    assert result.metrics.get("commit_reason") == "normal_gain"
    assert result.metrics.get("over_capacity_segments") == 0
    assert result.metrics.get("bottleneck_count") == 0


def test_pass3_degraded_commit_when_zero_gain() -> None:
    """Re-running on an already-optimized layout yields gain=0; degraded flag keeps commit."""

    asteroid_cells = {(x, y) for x in range(1, 14) for y in range(5)}
    mineable_cells = set(asteroid_cells)
    fixed_stub = (1, 2)
    anchor = (10, 2)
    original_transport = {fixed_stub: "pipe", anchor: "pipe"}
    for x in range(2, 10):
        original_transport[(x, 2)] = "pipe"
    for x in (5, 6, 7):
        original_transport[(x, 1)] = "pipe"
    optimal = reconstruct_mining_priority_transport(
        anchor=anchor,
        asteroid_cells=asteroid_cells,
        mineable_cells=mineable_cells,
        buildings={},
        transport_cells=original_transport,
        outlets_order=[fixed_stub],
        transport_role="pipe",
    )
    assert optimal.committed

    repeat = reconstruct_mining_priority_transport(
        anchor=anchor,
        asteroid_cells=asteroid_cells,
        mineable_cells=mineable_cells,
        buildings={},
        transport_cells=dict(optimal.transport_cells),
        outlets_order=[fixed_stub],
        transport_role="pipe",
        allow_degraded_connected_commit=False,
    )
    assert not repeat.committed
    assert repeat.metrics.get("rejected_reason") == "rejected_by_gain_or_length"

    degraded = reconstruct_mining_priority_transport(
        anchor=anchor,
        asteroid_cells=asteroid_cells,
        mineable_cells=mineable_cells,
        buildings={},
        transport_cells=dict(optimal.transport_cells),
        outlets_order=[fixed_stub],
        transport_role="pipe",
        allow_degraded_connected_commit=True,
    )
    assert degraded.committed
    assert degraded.metrics.get("commit_reason") == "degraded_connected_recovery"


def test_pass3_max_route_length_ratio_constant() -> None:
    assert MAX_ROUTE_LENGTH_RATIO == 1.35


def test_placement_stub_route_to_trunk_feasible_adjacent_stub() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        placement_stub_route_to_trunk_feasible,
    )

    anchor = (0, 0)
    stub = (1, 0)
    asteroid = {(0, 0), (1, 0)}
    mineable = set(asteroid)
    assert placement_stub_route_to_trunk_feasible(
        outlet_stub=stub,
        anchor=anchor,
        asteroid_cells=asteroid,
        mineable_cells=mineable,
        buildings={},
        transport_cells={anchor: "pipe", stub: "pipe"},
        fixed_stubs=frozenset({stub}),
    )


def test_placement_stub_route_probe_path_passes_buildings_to_cell_cost() -> None:
    """Regression (P3-E2.1): greedy baseline forwards ``buildings`` to cost like lex layout."""

    from unittest.mock import patch

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        placement_stub_route_probe_path,
    )

    anchor = (3, 0)
    stub = (1, 0)
    asteroid = {stub, (2, 0), anchor}
    mineable = set(asteroid)
    buildings = {(2, 0): "extractor"}
    tc = {anchor: "pipe", stub: "pipe", (2, 0): "pipe"}
    fs = frozenset({stub})
    seen: list[dict[str, object]] = []

    def capture(cell: tuple[int, int], **kw: Any) -> int:
        seen.append({"buildings": kw.get("buildings")})
        return mining_priority_route_cell_cost(cell, **kw)

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core."
        "mining_priority_route_cell_cost",
        side_effect=capture,
    ):
        placement_stub_route_probe_path(
            outlet_stub=stub,
            anchor=anchor,
            asteroid_cells=asteroid,
            mineable_cells=mineable,
            buildings=buildings,
            transport_cells=tc,
            fixed_stubs=fs,
        )
    assert seen, "expected cost function to be invoked"
    assert all(s.get("buildings") is buildings for s in seen), "buildings must not be dropped to {}"


def test_placement_stub_route_probe_path_matches_feasible() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        placement_stub_route_probe_path,
        placement_stub_route_to_trunk_feasible,
    )

    anchor = (0, 0)
    stub = (1, 0)
    asteroid = {(0, 0), (1, 0)}
    mineable = set(asteroid)
    tc = {anchor: "pipe", stub: "pipe"}
    fs = frozenset({stub})
    path = placement_stub_route_probe_path(
        outlet_stub=stub,
        anchor=anchor,
        asteroid_cells=asteroid,
        mineable_cells=mineable,
        buildings={},
        transport_cells=tc,
        fixed_stubs=fs,
    )
    assert path is not None
    assert path[0] == stub
    assert placement_stub_route_to_trunk_feasible(
        outlet_stub=stub,
        anchor=anchor,
        asteroid_cells=asteroid,
        mineable_cells=mineable,
        buildings={},
        transport_cells=tc,
        fixed_stubs=fs,
    )


def test_blocked_cells_omits_belt_and_probe_crosses_route_tree() -> None:
    """``blocked_cells``: belt not blocked; stub probe reuses existing transport (route_tree)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        placement_stub_route_probe_path,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
        blocked_cells,
    )

    cells = {
        (2, 0): {"role": "belt", "layout_kind": None},
        (10, 0): {"role": "occupied", "layout_kind": "miner"},
    }
    bl = blocked_cells(cells)
    assert (2, 0) not in bl
    assert (10, 0) in bl

    stub = (1, 0)
    anchor = (4, 0)
    asteroid = {stub, (2, 0), (3, 0), anchor}
    mineable = set(asteroid)
    buildings = {c: "occupied" for c in bl}
    tc = {stub: "belt", (2, 0): "belt", (3, 0): "belt", anchor: "belt"}
    path = placement_stub_route_probe_path(
        outlet_stub=stub,
        anchor=anchor,
        asteroid_cells=asteroid,
        mineable_cells=mineable,
        buildings=buildings,
        transport_cells=tc,
        fixed_stubs=frozenset({stub}),
    )
    assert path is not None
    assert (2, 0) in path and (3, 0) in path
