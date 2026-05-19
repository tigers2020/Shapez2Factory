"""Shared fixtures for ``tests/unit/asteroid_lab``."""

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
        ("SpacePipe_LeftTurn", "SpacePipe/SpacePipe_LeftTurn.svg"),
        ("SpacePipe_RightTurn", "SpacePipe/SpacePipe_RightTurn.svg"),
        ("SpacePipe_LeftFwdSplitter", "SpacePipe/SpacePipe_LeftFwdSplitter.svg"),
        ("SpacePipe_Forward", "SpacePipe/SpacePipe_Forward.svg"),
    ):
        ShapezGameIdentifier.objects.create(
            release=r,
            identifier_category=cat,
            value=value,
            normalized_value=value,
            sprite_static_relpath=rel,
        )
    return r


@pytest.fixture(params=range(len(load_reconstruction_fixture_line_pairs())))
def reconstruction_fixture_line_index(request: pytest.FixtureRequest) -> int:
    return int(request.param)
