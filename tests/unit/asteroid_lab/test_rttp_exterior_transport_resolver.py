"""EVTC-1b — exterior transport cap resolver (game_data DB SoT)."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from django_apps.asteroid_lab.contracts.rttp_exterior_throughput_tier import (
    ExteriorThroughputTier,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.rttp_exterior_transport_configuration import (
    ExteriorTransportCapacityConfigurationError,
)
from django_apps.asteroid_lab.services.rttp_exterior_transport_resolver import (
    space_belt_max_per_min,
    space_pipe_max_per_min,
    transport_max_throughput_per_min,
)
from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorShapeTransportCapacity,
)


@pytest.mark.django_db
def test_tier1_shape_space_belt_max_is_2880(imported_game_data_batch_module: object) -> None:
    _ = imported_game_data_batch_module
    assert space_belt_max_per_min(ExteriorThroughputTier.TIER_1) == Decimal("2880.0000")
    assert transport_max_throughput_per_min(
        TransportKind.SHAPE_BELT,
        tier=ExteriorThroughputTier.TIER_1,
    ) == Decimal("2880.0000")


@pytest.mark.django_db
def test_tier1_fluid_space_pipe_max_is_345600(imported_game_data_batch_module: object) -> None:
    _ = imported_game_data_batch_module
    assert space_pipe_max_per_min(ExteriorThroughputTier.TIER_1) == Decimal("345600.0000")
    assert transport_max_throughput_per_min(
        TransportKind.FLUID_PIPE,
        tier=ExteriorThroughputTier.TIER_1,
    ) == Decimal("345600.0000")


@pytest.mark.django_db
def test_missing_db_row_raises_configuration_error() -> None:
    active = ExteriorShapeTransportCapacity.objects.get(speed_tier=1, is_active=True)
    active.is_active = False
    active.save(update_fields=["is_active"])
    try:
        with pytest.raises(ExteriorTransportCapacityConfigurationError):
            space_belt_max_per_min(ExteriorThroughputTier.TIER_1)
    finally:
        active.is_active = True
        active.save(update_fields=["is_active"])


def test_resolver_modules_contain_no_evtc_cap_literals() -> None:
    """Caps must come from DB rows, not solver-local Decimal literals."""
    forbidden_str = frozenset({"2880", "345600", "1200", "288"})
    forbidden_num = frozenset({2880, 345600, 1200, 288})
    repo_root = Path(__file__).resolve().parents[3]
    paths = (
        repo_root / "django_apps/asteroid_lab/services/rttp_exterior_transport_resolver.py",
        repo_root / "django_apps/asteroid_lab/services/required_external_connectors.py",
    )
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            if isinstance(node.value, str) and node.value in forbidden_str:
                pytest.fail(f"literal {node.value!r} in {path.name}")
            if isinstance(node.value, (int, float)) and node.value in forbidden_num:
                pytest.fail(f"literal {node.value!r} in {path.name}")
