"""STEP 9 stub: quarantine surface + optional connectivity read-only probe."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.validation import (
    final_validation,
)


def test_quarantined_surfaces_as_geometry_not_ok() -> None:
    report = final_validation.validate_final_layout_stub(
        placement_commit_by_id={"x": PlacementCommitState.QUARANTINED_UNROUTED},
        transport_cells=frozenset(),
        external_cells=frozenset(),
    )
    assert report.quarantined_count == 1
    assert report.geometry_ok is False


def test_empty_transport_skips_connectivity_but_geometry_ok_when_clean() -> None:
    report = final_validation.validate_final_layout_stub(
        placement_commit_by_id={},
        transport_cells=frozenset(),
        external_cells=frozenset(),
    )
    assert report.geometry_ok is True
    assert report.connectivity_ok is True


def test_validate_final_layout_stub_does_not_replace_transport_or_external_sets() -> None:
    external = frozenset({(2, 0), (3, 0)})
    transport = frozenset({(2, 0), (4, 0)})
    ext_id = id(external)
    tr_id = id(transport)
    final_validation.validate_final_layout_stub(
        placement_commit_by_id={},
        transport_cells=transport,
        external_cells=external,
    )
    assert id(external) == ext_id
    assert id(transport) == tr_id
