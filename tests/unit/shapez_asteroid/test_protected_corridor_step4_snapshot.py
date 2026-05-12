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
