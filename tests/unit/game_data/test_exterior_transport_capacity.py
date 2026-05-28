"""EVTC-1a — Exterior transport capacity CANON rows (game_data SoT)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)
from django_apps.game_data.services.exterior_transport_capacity import (
    exterior_connector_count_for_throughput,
    exterior_line_count_for_throughput,
    get_active_exterior_fluid_transport_capacity,
    get_active_exterior_shape_transport_capacity,
    line_throughput_per_min_from_row,
    space_belt_connector_capacity_per_min_from_row,
    space_belt_max_per_min_from_row,
    space_pipe_max_per_min_from_row,
)


@pytest.mark.django_db
def test_seed_has_tier1_shape_and_fluid_active_rows() -> None:
    assert ExteriorShapeTransportCapacity.objects.filter(speed_tier=1, is_active=True).count() == 1
    assert ExteriorFluidTransportCapacity.objects.filter(speed_tier=1, is_active=True).count() == 1


def test_no_import_batch_field_on_capacity_models() -> None:
    for model in (ExteriorShapeTransportCapacity, ExteriorFluidTransportCapacity):
        names = {f.name for f in model._meta.get_fields()}
        assert "import_batch" not in names


@pytest.mark.django_db
def test_unique_active_shape_row_per_speed_tier() -> None:
    assert ExteriorShapeTransportCapacity.objects.filter(speed_tier=1, is_active=True).exists()
    with pytest.raises(IntegrityError):
        ExteriorShapeTransportCapacity.objects.create(
            speed_tier=1,
            mini_unit_output_per_min=Decimal("30"),
            buildings_per_regular_belt=4,
            miner_full_output_multiplier=16,
            lanes_per_line=12,
            lines_per_space_belt=12,
            space_belt_full_belt_count=48,
            is_active=True,
        )


@pytest.mark.django_db
def test_shape_tier1_space_belt_rates_from_db() -> None:
    row = get_active_exterior_shape_transport_capacity(speed_tier=1)
    assert row.source_kind == ExteriorShapeTransportCapacity.SourceKind.EVTC_CANON
    assert row.mini_unit_output_per_min == Decimal("30.0000")
    assert row.miner_full_output_multiplier == 16
    inner = row.mini_unit_output_per_min * Decimal(row.buildings_per_regular_belt)
    assert inner == Decimal("120")
    assert line_throughput_per_min_from_row(row) == Decimal("480")
    assert space_belt_connector_capacity_per_min_from_row(row) == Decimal("5760")
    assert space_belt_max_per_min_from_row(row) == Decimal("5760")


@pytest.mark.django_db
def test_exterior_connector_count_ceil_shape_throughput() -> None:
    assert (
        exterior_connector_count_for_throughput(
            Decimal("960"),
            resource_kind="shape",
        )
        == 1
    )
    assert (
        exterior_connector_count_for_throughput(
            Decimal("5761"),
            resource_kind="shape",
        )
        == 2
    )
    assert (
        exterior_connector_count_for_throughput(
            Decimal("69960"),
            resource_kind="shape",
        )
        == 13
    )
    assert (
        exterior_line_count_for_throughput(
            Decimal("69960"),
            resource_kind="shape",
        )
        == 146
    )
    assert exterior_connector_count_for_throughput(Decimal("0"), resource_kind="shape") == 0


@pytest.mark.django_db
def test_fluid_tier1_space_pipe_max_is_345600_from_db() -> None:
    row = get_active_exterior_fluid_transport_capacity(speed_tier=1)
    assert row.source_kind == ExteriorFluidTransportCapacity.SourceKind.EVTC_CANON
    assert space_pipe_max_per_min_from_row(row) == Decimal("345600")


def test_service_has_no_rttp_imports() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(
        Path("django_apps/game_data/services/exterior_transport_capacity.py").read_text(
            encoding="utf-8"
        )
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "asteroid_lab" not in node.module
            assert "shapez_asteroid" not in node.module
