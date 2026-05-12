"""PlacementCommitState helpers (Algorithm §9.6 alignment)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    transition_placement_record_to_rolled_back,
)


def test_transition_to_rolled_back_preserves_rollback_reason() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000001",
        placement_pass="pass1",
        extractor_cell=(1, 1),
        extension_cells=(),
        stub_cell=(2, 1),
        transport_kind="shape_belt",
        state=PlacementCommitState.QUARANTINED_UNROUTED,
        route_id="route-x",
        rollback_reason="no_route",
    )
    out = transition_placement_record_to_rolled_back(rec)
    assert out.state == PlacementCommitState.ROLLED_BACK
    assert out.rollback_reason == "no_route"
    assert out.route_id is None


def test_transition_to_rolled_back_explicit_reason() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000002",
        placement_pass="pass1",
        extractor_cell=(3, 1),
        extension_cells=(),
        stub_cell=(4, 1),
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
        route_id="route-y",
        rollback_reason=None,
    )
    out = transition_placement_record_to_rolled_back(
        rec,
        rollback_reason="p2c_trunk_disconnect",
    )
    assert out.state == PlacementCommitState.ROLLED_BACK
    assert out.rollback_reason == "p2c_trunk_disconnect"
    assert out.route_id is None
