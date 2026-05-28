"""Shared fixtures for ``tests/unit/asteroid_lab`` (reconstruction / genetic_sample)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.reconstruction.topology_contract import (
    load_reconstruction_fixture_line_pairs,
)
from django_apps.shapez_core.models import (
    ShapezBasedataRelease,
    ShapezGameIdentifier,
    ShapezIdentifierCategory,
)


@pytest.fixture
def lab_sprite_identifiers_for_admin() -> ShapezBasedataRelease:
    r = ShapezBasedataRelease.objects.create(
        game_version=900_043,
        notes="genetic-lab-sprite-test",
        integrity_status_id=ShapezBasedataRelease.IntegrityStatus.IMPORTED.value,
    )
    cat = ShapezIdentifierCategory.objects.create(release=r, key="BuildingVariantIds", sort_order=0)
    for value, rel in (
        ("Layout_ProMiner", "web/img/lab/Layout_ProMiner.png"),
        ("SpaceBelt_Left", "web/img/lab/SpaceBelt_Left.png"),
    ):
        ShapezGameIdentifier.objects.create(
            release=r,
            category=cat,
            value=value,
            sprite_relpath=rel,
        )
    return r


@pytest.fixture(params=range(len(load_reconstruction_fixture_line_pairs())))
def reconstruction_fixture_line_index(request: pytest.FixtureRequest) -> int:
    return int(request.param)
