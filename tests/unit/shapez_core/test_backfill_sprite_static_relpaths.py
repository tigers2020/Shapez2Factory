"""Unit tests for backfill_sprite_static_relpaths management command."""

from __future__ import annotations

import json

import pytest
from django.core.management import call_command

from django_apps.shapez_core.models import ShapezGameIdentifier


@pytest.mark.django_db
def test_backfill_updates_stale_space_belt_relpath(tmp_path) -> None:
    """Rows with empty sprite_static_relpath are updated when SVG files exist."""
    from django_apps.shapez_core.services.basedata_import_service import import_basedata_bundle

    root = tmp_path / "basedata-v999011"
    root.mkdir(parents=True)
    (root / "version").write_text("999011", encoding="utf-8")
    identifiers = {
        "BuildingVariantIds": ["SpaceBelt_Forward", "SpacePipe_Forward"],
        "BuildingInternalVariantIds": [],
        "IslandLayoutIds": [],
        "WikiEntryIds": [],
        "ImageIds": [],
        "VideoIds": [],
        "IconIds": [],
    }
    (root / "identifiers.json").write_text(json.dumps(identifiers), encoding="utf-8")
    buildings = [
        {"Id": "SpaceBelt_Forward", "InternalVariants": []},
        {"Id": "SpacePipe_Forward", "InternalVariants": []},
    ]
    (root / "buildings.json").write_text(json.dumps(buildings), encoding="utf-8")

    rel = import_basedata_bundle(root, replace=False)
    belt_id = rel.game_identifiers.filter(value="SpaceBelt_Forward").first()
    pipe_id = rel.game_identifiers.filter(value="SpacePipe_Forward").first()
    assert belt_id is not None
    assert pipe_id is not None

    # Simulate stale DB: clear the relpath as if SVGs didn't exist at import time.
    ShapezGameIdentifier.objects.filter(pk__in=[belt_id.pk, pipe_id.pk]).update(
        sprite_static_relpath=""
    )
    belt_id.refresh_from_db()
    pipe_id.refresh_from_db()
    assert belt_id.sprite_static_relpath == ""
    assert pipe_id.sprite_static_relpath == ""

    call_command("backfill_sprite_static_relpaths")

    belt_id.refresh_from_db()
    pipe_id.refresh_from_db()
    assert belt_id.sprite_static_relpath == "SpaceBelt/SpaceBelt_Forward.svg"
    assert pipe_id.sprite_static_relpath == "SpacePipe/SpacePipe_Forward.svg"


@pytest.mark.django_db
def test_backfill_does_not_overwrite_correct_relpath(tmp_path) -> None:
    """Rows already holding the correct path are untouched (bulk_update skips them)."""
    from django_apps.shapez_core.services.basedata_import_service import import_basedata_bundle

    root = tmp_path / "basedata-v999012"
    root.mkdir(parents=True)
    (root / "version").write_text("999012", encoding="utf-8")
    identifiers = {
        "BuildingVariantIds": ["SpaceBelt_Forward"],
        "BuildingInternalVariantIds": [],
        "IslandLayoutIds": [],
        "WikiEntryIds": [],
        "ImageIds": [],
        "VideoIds": [],
        "IconIds": [],
    }
    (root / "identifiers.json").write_text(json.dumps(identifiers), encoding="utf-8")
    buildings = [{"Id": "SpaceBelt_Forward", "InternalVariants": []}]
    (root / "buildings.json").write_text(json.dumps(buildings), encoding="utf-8")

    rel = import_basedata_bundle(root, replace=False)
    belt_id = rel.game_identifiers.filter(value="SpaceBelt_Forward").first()
    assert belt_id is not None
    # Import already sets correct path; command should leave it unchanged.
    expected = belt_id.sprite_static_relpath

    call_command("backfill_sprite_static_relpaths")

    belt_id.refresh_from_db()
    assert belt_id.sprite_static_relpath == expected
