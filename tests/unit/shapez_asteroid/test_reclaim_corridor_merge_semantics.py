"""Reclaim vs replay overlay corridor merge semantics (intentionally different)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_read_factory import (  # noqa: E501
    protected_corridors_read_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    _corridors_from_solver_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_corridors import (  # noqa: E501
    protected_corridors_overlay_from_routing_state,
)


def test_reclaim_nested_hard_overrides_flat_hard_replay_overlay_keeps_flat() -> None:
    """Same routing_state: reclaim nested hard wins; replay overlay keeps non-empty flat hard."""

    rs = {
        "hard_protected_corridors": [[9, 9]],
        "protected_corridors": {"hard": [[1, 2]], "soft": []},
    }
    overlay = protected_corridors_overlay_from_routing_state(rs)
    assert overlay["hard"] == [[9, 9]]

    replay_dto = protected_corridors_read_from_routing_state(rs)
    assert replay_dto.hard == {(9, 9)}

    reclaim_sets = _corridors_from_solver_routing_state(rs)
    assert reclaim_sets.hard == {(1, 2)}
