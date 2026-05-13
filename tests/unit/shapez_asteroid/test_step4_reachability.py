"""``step4_reachability`` — Pass2 bounded STEP4-legality precheck (no Dijkstra)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_reachability as s4r,
)


def _cells(mineable: frozenset[Coord]) -> dict[Coord, dict]:
    return {
        c: {
            "x": c[0],
            "y": c[1],
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        }
        for c in mineable
    }


def test_precheck_stub_isolated_before_bfs() -> None:
    mineable = frozenset(
        {
            (4, 5),
            (5, 5),
            (6, 5),
            (5, 4),
            (5, 6),
            (7, 5),
        }
    )
    blocked = frozenset({(4, 5), (6, 5), (5, 4), (5, 6)})
    cells = _cells(mineable)
    prec = s4r.pass2_stub_bounded_step4_reachability_precheck(
        stub_cell=(5, 5),
        want_role="belt",
        transport_kind="shape_belt",
        cells_base=cells,
        transport_probe=frozenset({(5, 5)}),
        blocked_probe=blocked,
        mineable=mineable,
        asteroid=frozenset(),
        is_external=lambda c: c[0] >= 100,
        goal_cells=frozenset({(7, 5)}),
        trunk_cells=frozenset({(7, 5)}),
        margin_cells=set(),
    )
    assert prec.stub_isolated_geometry is True
    assert prec.stop_reason == "stub_isolated"
    assert prec.visits == 0
    assert prec.reachable is False


def test_precheck_unreachable_exhausted_dead_end() -> None:
    """Pocket + isolated goal cell in ``mineable`` with no STEP4-legal corridor between them."""

    mineable = frozenset({(5, 5), (6, 5), (20, 20)})
    cells = _cells(mineable)
    blocked = frozenset({(4, 5), (5, 4), (5, 6), (7, 5), (6, 4), (6, 6)})
    prec = s4r.pass2_stub_bounded_step4_reachability_precheck(
        stub_cell=(5, 5),
        want_role="belt",
        transport_kind="shape_belt",
        cells_base=cells,
        transport_probe=frozenset({(5, 5)}),
        blocked_probe=blocked,
        mineable=mineable,
        asteroid=frozenset(),
        is_external=lambda c: c[0] >= 100,
        goal_cells=frozenset({(20, 20)}),
        trunk_cells=frozenset({(20, 20)}),
        margin_cells=set(),
    )
    assert prec.stub_isolated_geometry is False
    assert prec.stop_reason == "exhausted"
    assert prec.reachable_goal_count == 0
    assert prec.reachable is False


def test_precheck_success_reaches_trunk_goal() -> None:
    mineable = frozenset(
        {
            (5, 0),
            (6, 0),
            (7, 0),
            (8, 0),
            (9, 0),
            (10, 0),
        }
    )
    cells = _cells(mineable)
    transport = frozenset({(5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0)})
    blocked = frozenset({(2, 0)})
    trunk = frozenset({(10, 0)})
    goals = frozenset({(10, 0), (11, 0)})
    prec = s4r.pass2_stub_bounded_step4_reachability_precheck(
        stub_cell=(5, 0),
        want_role="belt",
        transport_kind="shape_belt",
        cells_base=cells,
        transport_probe=transport,
        blocked_probe=blocked,
        mineable=mineable,
        asteroid=frozenset(),
        is_external=lambda c: c[0] >= 100,
        goal_cells=goals,
        trunk_cells=trunk,
        margin_cells={(11, 0)},
    )
    assert prec.stub_isolated_geometry is False
    assert prec.stop_reason == "success"
    assert prec.reachable is True
    assert prec.reachable_goal_count >= 1
