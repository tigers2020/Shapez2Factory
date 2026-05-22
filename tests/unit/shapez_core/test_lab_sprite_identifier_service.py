"""Identifier-backed lab sprite path map."""

from __future__ import annotations

import pytest

from django_apps.shapez_core.models import (
    ShapezBasedataRelease,
    ShapezGameIdentifier,
    ShapezIdentifierCategory,
)
from django_apps.shapez_core.services.lab_sprite_identifier_service import (
    build_lab_identifier_sprite_relpath_map,
    get_lab_sprite_relpath_for_value,
)


@pytest.fixture
def lab_sprite_release_with_identifiers() -> ShapezBasedataRelease:
    r = ShapezBasedataRelease.objects.create(
        game_version=900_042,
        notes="lab-sprite-id-test",
        integrity_status_id=ShapezBasedataRelease.IntegrityStatus.IMPORTED.value,
    )
    cat = ShapezIdentifierCategory.objects.create(release=r, key="BuildingVariantIds", sort_order=0)
    ShapezGameIdentifier.objects.create(
        release=r,
        identifier_category=cat,
        value="SpacePipe_Forward",
        normalized_value="SpacePipe_Forward",
        sprite_static_relpath="SpacePipe/SpacePipe_Forward.svg",
    )
    return r


@pytest.mark.django_db
def test_get_lab_sprite_relpath_for_value(
    lab_sprite_release_with_identifiers: ShapezBasedataRelease,
) -> None:
    rid = lab_sprite_release_with_identifiers.pk
    assert get_lab_sprite_relpath_for_value("SpacePipe_Forward", release_id=rid) == (
        "SpacePipe/SpacePipe_Forward.svg"
    )
    assert get_lab_sprite_relpath_for_value("Missing_T", release_id=rid) == ""


@pytest.mark.django_db
def test_build_lab_identifier_sprite_relpath_map(
    lab_sprite_release_with_identifiers: ShapezBasedataRelease,
) -> None:
    m = build_lab_identifier_sprite_relpath_map(release_id=lab_sprite_release_with_identifiers.pk)
    assert m.get("SpacePipe_Forward") == "SpacePipe/SpacePipe_Forward.svg"
    assert m.get("Layout_ShapeMiner") == "Miner/Layout_ShapeMiner.svg"
    m_all = build_lab_identifier_sprite_relpath_map()
    assert m_all.get("SpacePipe_Forward") == "SpacePipe/SpacePipe_Forward.svg"
    assert m_all.get("Layout_ProMiner") == "Miner/Layout_ShapeMiner.svg"


def test_build_lab_identifier_sprite_relpath_map_without_db() -> None:
    m = build_lab_identifier_sprite_relpath_map()
    assert m.get("SpaceBelt_LeftTurn") == "SpaceBelt/SpaceBelt_LeftTurn.svg"
    assert m.get("SpaceBelt_Left") == "SpaceBelt/SpaceBelt_LeftTurn.svg"
