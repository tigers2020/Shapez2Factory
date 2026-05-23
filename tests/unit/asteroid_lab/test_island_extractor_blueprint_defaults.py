"""Canonical island extractor blueprints (balance / omni / fluid)."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.catalog.island_extractor_defaults import (
    EXPECTED_INNER_FINGERPRINTS,
    ISLAND_EXTRACTOR_DEFAULTS,
    IslandExtractorVariantKey,
    default_record,
    inner_building_type_counts,
    inner_entry_fingerprint,
)
from django_apps.asteroid_lab.models import IslandExtractorBlueprint
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy


@pytest.mark.parametrize("row", ISLAND_EXTRACTOR_DEFAULTS, ids=lambda r: r.variant_key.value)
def test_catalog_copy_decodes_and_layout_t_matches(row) -> None:
    root = decode_shapez2_copy(row.copy_code)
    top = root["BP"]["Entries"][0]
    assert top.get("T") == row.layout_t
    assert inner_entry_fingerprint(row.copy_code) == EXPECTED_INNER_FINGERPRINTS[row.variant_key]


def test_shape_balance_vs_omni_inner_fingerprints_differ() -> None:
    balance = inner_entry_fingerprint(
        default_record(IslandExtractorVariantKey.SHAPE_BALANCE).copy_code
    )
    omni = inner_entry_fingerprint(default_record(IslandExtractorVariantKey.SHAPE_OMNI).copy_code)
    assert balance != omni


def test_shape_balance_has_more_belt_port_senders_than_omni() -> None:
    balance_code = default_record(IslandExtractorVariantKey.SHAPE_BALANCE).copy_code
    omni_code = default_record(IslandExtractorVariantKey.SHAPE_OMNI).copy_code
    balance_counts = inner_building_type_counts(balance_code)
    omni_counts = inner_building_type_counts(omni_code)
    belt_sender = "BeltPortSenderInternalVariant"
    assert balance_counts[belt_sender] > omni_counts[belt_sender]
    assert omni_counts["TrashDefaultInternalVariant"] > 0


@pytest.mark.django_db
def test_seed_island_extractor_blueprints_command() -> None:
    call_command("seed_island_extractor_blueprints")
    assert IslandExtractorBlueprint.objects.count() == 3
    balance_key = IslandExtractorVariantKey.SHAPE_BALANCE
    balance = IslandExtractorBlueprint.objects.get(variant_key=balance_key.value)
    assert balance.layout_t == "Layout_ShapeMiner"
    assert balance.inner_fingerprint == EXPECTED_INNER_FINGERPRINTS[balance_key]
    fluid_key = IslandExtractorVariantKey.FLUID_DEFAULT
    fluid = IslandExtractorBlueprint.objects.get(variant_key=fluid_key.value)
    assert fluid.layout_t == "Layout_FluidMiner"
    assert inner_building_type_counts(fluid.copy_code)["PumpDefaultInternalVariant"] == 16
