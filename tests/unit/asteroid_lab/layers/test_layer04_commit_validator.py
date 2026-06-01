"""Layer 04 commit validator (PR-L4-2)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.commit_validator import (  # noqa: E501
    L4CommitValidator,
)


def test_rejects_belt_on_miner_cell() -> None:
    miner = (2, 2)
    validator = L4CommitValidator(
        equipment_cells=frozenset({miner}),
        connector_cells=frozenset({(5, 2)}),
        stub_cells=frozenset({(3, 2)}),
    )
    err = validator.validate_route_cell(miner)
    assert err is Layer04FailureReason.COMMIT_OVERLAP_BLOCKED


def test_allows_connector_attachment_cell() -> None:
    connector = (5, 2)
    validator = L4CommitValidator(
        equipment_cells=frozenset({(2, 2)}),
        connector_cells=frozenset({connector}),
        stub_cells=frozenset({(3, 2)}),
    )
    assert validator.validate_route_cell(connector) is None


def test_allows_stub_cell() -> None:
    stub = (3, 2)
    validator = L4CommitValidator(
        equipment_cells=frozenset({(2, 2)}),
        connector_cells=frozenset({(5, 2)}),
        stub_cells=frozenset({stub}),
    )
    assert validator.validate_route_cell(stub) is None


def test_allows_void_route_cell() -> None:
    validator = L4CommitValidator(
        equipment_cells=frozenset({(2, 2)}),
        connector_cells=frozenset({(5, 2)}),
        stub_cells=frozenset({(3, 2)}),
    )
    assert validator.validate_route_cell((4, 2)) is None
