"""PR-1 — MiningExtractionRule CANON_MANUAL seed and helpers."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from django_apps.game_data.models.mining import MiningExtractionRule
from django_apps.game_data.services.mining_extraction_rules import (
    VALID_THROUGHPUT_FACTORS,
    assert_throughput_factor_matches_extensions,
    effective_mini_units,
    get_active_rule,
    max_output_per_miner,
    output_per_min,
)


@pytest.mark.django_db
def test_seed_has_shape_and_fluid_active_rules() -> None:
    assert MiningExtractionRule.objects.filter(resource_kind="shape", is_active=True).count() == 1
    assert MiningExtractionRule.objects.filter(resource_kind="fluid", is_active=True).count() == 1


def test_no_import_batch_field_on_rule_model() -> None:
    names = {f.name for f in MiningExtractionRule._meta.get_fields()}
    assert "import_batch" not in names


def test_no_fluid_pipe_capacity_field_on_rule_model() -> None:
    names = {f.name for f in MiningExtractionRule._meta.get_fields()}
    assert "fluid_pipe_capacity" not in names
    assert "fluid_pipe_capacity_per_min" not in names


@pytest.mark.django_db
def test_unique_active_rule_per_resource() -> None:
    """Seed already inserted active shape; second active row violates partial unique."""
    with pytest.raises(IntegrityError):
        MiningExtractionRule.objects.create(
            resource_kind=MiningExtractionRule.ResourceKind.SHAPE,
            transport_kind="shape_belt",
            mini_unit_output_per_min=Decimal("30"),
            output_unit="shapes_per_min",
            is_active=True,
        )


@pytest.mark.django_db
def test_inactive_duplicate_rule_allowed() -> None:
    row = MiningExtractionRule.objects.create(
        resource_kind=MiningExtractionRule.ResourceKind.SHAPE,
        transport_kind="shape_belt",
        mini_unit_output_per_min=Decimal("30"),
        output_unit="shapes_per_min",
        is_active=False,
    )
    assert row.pk is not None


@pytest.mark.django_db
def test_shape_max_output_is_480() -> None:
    rule = get_active_rule("shape")
    assert max_output_per_miner(rule) == Decimal("480.0000")


@pytest.mark.django_db
def test_fluid_max_output_is_4800() -> None:
    rule = get_active_rule("fluid")
    assert max_output_per_miner(rule) == Decimal("4800.0000")


def test_effective_mini_units_0_to_3() -> None:
    assert effective_mini_units(0) == 4
    assert effective_mini_units(1) == 8
    assert effective_mini_units(2) == 12
    assert effective_mini_units(3) == 16


def test_effective_mini_units_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        effective_mini_units(4)


@pytest.mark.django_db
def test_output_per_min_uses_decimal() -> None:
    rule = get_active_rule("shape")
    assert output_per_min(rule, 8) == Decimal("240.0000")


def test_assert_throughput_factor_matches_extensions() -> None:
    assert_throughput_factor_matches_extensions(12, 2)


def test_valid_throughput_factors_match_pattern_library() -> None:
    assert VALID_THROUGHPUT_FACTORS == frozenset({4, 8, 12, 16})


def test_service_has_no_rttp_imports() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(
        Path("django_apps/game_data/services/mining_extraction_rules.py").read_text(
            encoding="utf-8"
        )
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "asteroid_lab" not in node.module
            assert "shapez_asteroid" not in node.module
