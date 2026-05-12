"""§14.2 STEP4 committed-route routing_state: candidate vs confirmed soft pool."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_NO_REPLACEMENT_ROUTE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3 import (
    pass3_e3_guarded_atomic_map as _p3e3_atomic,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_state import (
    _routing_state_from_committed_routes,
)


def _hard_coords(rs: dict) -> set[tuple[int, int]]:
    return {tuple(int(x) for x in c) for c in rs.get("hard_protected_corridors") or []}


def _soft_coords(rs: dict) -> set[tuple[int, int]]:
    return {tuple(int(x) for x in c) for c in rs.get("soft_protected_corridors") or []}


def test_routing_state_from_committed_routes_leaves_soft_candidate_pool_empty() -> None:
    """Committed routes only: ``soft_protected_candidate_corridors`` stays empty."""

    route = Step4Route(
        extractor_cell=(1, 1),
        stub_cell=(1, 2),
        transport_kind="shape_belt",
        path=((1, 3), (1, 4)),
        merged_to_existing=False,
        reached_external=True,
        placement_id="p0",
    )
    rs = _routing_state_from_committed_routes((route,))
    assert rs is not None
    assert rs["soft_protected_candidate_corridors"] == []
    assert rs["soft_protected_confirmed_corridors"] == rs["soft_protected_corridors"]
    assert rs["soft_protected_confirmed_corridors"]
    assert "ela_trunk_seed_candidate_corridors" not in rs


def test_routing_state_el_trunk_seed_candidate_key_serializes_ela() -> None:
    """ELA present: ``ela_trunk_seed_candidate_corridors`` mirrors ``trunk_seed_cell_union``."""

    route = Step4Route(
        extractor_cell=(9, 9),
        stub_cell=(10, 1),
        transport_kind="shape_belt",
        path=((10, 2), (10, 3), (10, 4)),
        merged_to_existing=False,
        reached_external=True,
        placement_id="p1",
    )
    ela = {
        "solver_hints": {
            "trunk_seed_cell_union": [[10, 2], [10, 3], [99, 1]],
            "cleanup_candidate_cell_union": [],
        }
    }
    rs = _routing_state_from_committed_routes((route,), existing_layout_analysis=ela)
    assert rs is not None
    assert rs["ela_trunk_seed_candidate_corridors"] == [[99, 1], [10, 2], [10, 3]]
    hard = _hard_coords(rs)
    assert hard == {(10, 1), (10, 4)}


def test_routing_state_el_trunk_seed_mid_path_not_hard() -> None:
    """Path interior cells listed as ELA trunk seeds stay soft, not hard (§14 / PR4-C)."""

    route = Step4Route(
        extractor_cell=(9, 9),
        stub_cell=(10, 1),
        transport_kind="shape_belt",
        path=((10, 2), (10, 3), (10, 4)),
        merged_to_existing=False,
        reached_external=True,
        placement_id="p1",
    )
    ela = {
        "solver_hints": {
            "trunk_seed_cell_union": [[10, 2], [10, 3]],
            "cleanup_candidate_cell_union": [],
        }
    }
    rs = _routing_state_from_committed_routes((route,), existing_layout_analysis=ela)
    assert rs is not None
    hard, soft = _hard_coords(rs), _soft_coords(rs)
    assert (10, 2) in soft and (10, 2) not in hard
    assert (10, 3) in soft and (10, 3) not in hard
    assert (10, 1) in hard and (10, 4) in hard


def test_p3e3_atomic_rejects_soft_cells_removed_without_replacement_route() -> None:
    soft = frozenset({(2, 2), (2, 3)})
    cand = _p3e3_atomic._p3e3_build_atomic_candidate_map(
        current_transport_cells=frozenset({(2, 2), (2, 3), (5, 5)}),
        cells_to_remove=frozenset({(2, 2)}),
        replacement_route_cells=frozenset(),
        fixed_output_stubs=frozenset(),
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=soft,
        baseline_route_length=3,
        candidate_route_length=3,
    )
    assert cand.precheck_passed is False
    assert cand.rejected_reason == P3E3_REJECT_NO_REPLACEMENT_ROUTE
