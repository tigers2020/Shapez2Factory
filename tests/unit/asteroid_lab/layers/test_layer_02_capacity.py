"""EVTC capacity adapter tests (PR-CLI-2b: port injection + ORM/snapshot parity)."""

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.adapters.orm_game_data_rules import (
    build_game_data_snapshot_payload,
    build_orm_game_data_rules,
)
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
from shapez2_factory.domain.asteroid_lab.exterior_capacity_row import ExteriorCapacityRow


class _RaisingRules:
    """Port stub whose row lookup always fails (no DB)."""

    def exterior_connector_capacity(
        self,
        *,
        resource_kind: str,
        speed_tier: int,
    ) -> ExteriorCapacityRow:
        raise LookupError(f"no row for {resource_kind!r} {speed_tier!r}")


@pytest.mark.django_db
def test_orm_snapshot_parity_matches_evtc_service() -> None:
    expected_row = get_active_exterior_shape_transport_capacity(speed_tier=1)
    expected = space_belt_connector_capacity_per_min_from_row(expected_row)

    rules = build_orm_game_data_rules()
    got = rules.exterior_connector_capacity(resource_kind="shape", speed_tier=1)

    assert got.per_connector_capacity_per_min == expected
    assert got.per_connector_capacity_per_min > 0


@pytest.mark.django_db
def test_snapshot_payload_carries_resolver_output() -> None:
    payload = build_game_data_snapshot_payload()
    shape_rows = [
        r for r in payload["exterior_transport_capacity"] if r["resource_kind"] == "shape"
    ]
    expected = space_belt_connector_capacity_per_min_from_row(
        get_active_exterior_shape_transport_capacity(speed_tier=1)
    )

    tier1 = next(r for r in shape_rows if r["speed_tier"] == 1)
    assert Decimal(tier1["per_connector_capacity_per_min"]) == expected


@pytest.mark.django_db
def test_snapshot_payload_carries_mining_extraction_rules() -> None:
    from django_apps.game_data.services.mining_extraction_rules import get_active_rule

    payload = build_game_data_snapshot_payload()
    shape_row = next(
        r for r in payload["mining_extraction_rules"] if r["resource_kind"] == "shape"
    )
    rule = get_active_rule("shape")

    assert Decimal(shape_row["mini_unit_output_per_min"]) == rule.mini_unit_output_per_min
    assert shape_row["output_unit"] == rule.output_unit


@pytest.mark.django_db
def test_shape_capacity_via_injected_orm_rules() -> None:
    rules = build_orm_game_data_rules()
    expected = space_belt_connector_capacity_per_min_from_row(
        get_active_exterior_shape_transport_capacity(speed_tier=1)
    )

    got = resolve_per_connector_capacity(rules=rules, resource_kind="shape", speed_tier=1)

    assert got.shortfall_reason is None
    assert got.capacity_per_min == expected


def test_missing_evtc_row_returns_missing_evtc_reason() -> None:
    got = resolve_per_connector_capacity(
        rules=_RaisingRules(),
        resource_kind="shape",
        speed_tier=99,
    )

    assert got.capacity_per_min is None
    assert got.shortfall_reason == ExteriorConnectionShortfallReason.MISSING_EVTC_ROW


def test_layout_t_shape_base() -> None:
    assert default_exterior_connector_layout_t(resource_kind="shape") == "SpaceBelt_Forward"


def test_layout_t_fluid_base() -> None:
    assert default_exterior_connector_layout_t(resource_kind="fluid") == "SpacePipe_Forward"
