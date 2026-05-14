from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.validation.final_validation import (  # noqa: E501
    validate_final_layout_stub,
)


def test_validation_rejects_quarantined() -> None:
    rep = validate_final_layout_stub(
        placement_commit_by_id={"a": PlacementCommitState.QUARANTINED_UNROUTED},
        transport_cells=frozenset(),
        external_cells=frozenset(),
    )
    assert rep.geometry_ok is False
    assert rep.quarantined_count == 1


def test_validation_accepts_empty_transport() -> None:
    rep = validate_final_layout_stub(
        placement_commit_by_id={},
        transport_cells=frozenset(),
        external_cells=frozenset(),
    )
    assert rep.geometry_ok is True
