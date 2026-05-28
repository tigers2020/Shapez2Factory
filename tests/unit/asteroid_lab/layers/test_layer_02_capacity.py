"""EVTC capacity adapter tests."""

import pytest

from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.capacity import (
    resolve_per_connector_capacity,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.layout_t import (
    default_exterior_connector_layout_t,
)
from django_apps.game_data.services.exterior_transport_capacity import (
    get_active_exterior_shape_transport_capacity,
    space_belt_connector_capacity_per_min_from_row,
)


@pytest.mark.django_db
def test_shape_capacity_uses_evtc_service() -> None:
    row = get_active_exterior_shape_transport_capacity(speed_tier=1)
    expected = space_belt_connector_capacity_per_min_from_row(row)

    got = resolve_per_connector_capacity(resource_kind="shape", speed_tier=1)

    assert got.shortfall_reason is None
    assert got.capacity_per_min == expected
    assert got.capacity_per_min is not None
    assert got.capacity_per_min > 0


@pytest.mark.django_db
def test_missing_evtc_row_returns_missing_evtc_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(**_kwargs: object) -> object:
        raise LookupError("no row")

    monkeypatch.setattr(
        "django_apps.asteroid_lab.layers.layer_02_exterior_transport.capacity."
        "get_active_exterior_shape_transport_capacity",
        _boom,
    )

    got = resolve_per_connector_capacity(resource_kind="shape", speed_tier=99)

    assert got.capacity_per_min is None
    assert got.shortfall_reason == ExteriorConnectionShortfallReason.MISSING_EVTC_ROW


def test_layout_t_shape_base() -> None:
    assert default_exterior_connector_layout_t(resource_kind="shape") == "SpaceBelt_Forward"


def test_layout_t_fluid_base() -> None:
    assert default_exterior_connector_layout_t(resource_kind="fluid") == "SpacePipe_Forward"
