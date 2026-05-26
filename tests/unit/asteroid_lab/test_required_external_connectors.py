"""EVTC-1b — required exterior connector ceildiv."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.contracts.rttp_exterior_throughput_tier import (
    ExteriorThroughputTier,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.required_external_connectors import (
    required_external_connectors,
)


@pytest.mark.django_db
def test_ceildiv_tier1_shape_two_connectors_for_5760_asteroid_max(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    assert (
        required_external_connectors(
            max_asteroid_throughput_per_min=Decimal("5760"),
            transport_kind=TransportKind.SHAPE_BELT,
            tier=ExteriorThroughputTier.TIER_1,
        )
        == 2
    )


@pytest.mark.django_db
def test_ceildiv_tier1_fluid_two_connectors_for_345601(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    assert (
        required_external_connectors(
            max_asteroid_throughput_per_min=Decimal("345601"),
            transport_kind=TransportKind.FLUID_PIPE,
            tier=ExteriorThroughputTier.TIER_1,
        )
        == 2
    )


@pytest.mark.django_db
def test_zero_or_negative_numerator_returns_zero(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    assert (
        required_external_connectors(
            max_asteroid_throughput_per_min=Decimal("0"),
            transport_kind=TransportKind.SHAPE_BELT,
        )
        == 0
    )
    assert (
        required_external_connectors(
            max_asteroid_throughput_per_min=Decimal("-1"),
            transport_kind=TransportKind.FLUID_PIPE,
        )
        == 0
    )
