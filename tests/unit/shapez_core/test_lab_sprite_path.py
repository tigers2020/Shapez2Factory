"""Lab sprite path resolution for ``ShapezGameIdentifier.value``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.shapez_core.lab_sprite_path import (
    default_lab_sprites_root,
    resolve_sprite_static_relpath,
)


def test_resolve_sprite_static_relpath_unknown_prefix() -> None:
    root = Path("/nonexistent/sprites")
    assert resolve_sprite_static_relpath("Wiki_Foo", sprites_root=root) == ""


def test_resolve_sprite_static_relpath_missing_file(tmp_path: Path) -> None:
    root = tmp_path / "sprites"
    (root / "SpacePipe").mkdir(parents=True)
    assert resolve_sprite_static_relpath("SpacePipe_Forward", sprites_root=root) == ""


def test_resolve_sprite_static_relpath_when_present(tmp_path: Path) -> None:
    root = tmp_path / "sprites"
    d = root / "SpacePipe"
    d.mkdir(parents=True)
    (d / "SpacePipe_Forward.svg").write_text("<svg/>", encoding="utf-8")
    assert resolve_sprite_static_relpath("SpacePipe_Forward", sprites_root=root) == (
        "SpacePipe/SpacePipe_Forward.svg"
    )


def test_default_lab_sprites_root_points_under_django_apps() -> None:
    p = default_lab_sprites_root()
    assert p.name == "sprites"
    assert "static" in p.parts


@pytest.mark.django_db
def test_import_sets_sprite_static_relpath_when_asset_exists(tmp_path: Path) -> None:
    from django_apps.shapez_core.services.basedata_import_service import import_basedata_bundle

    root = tmp_path / "basedata-v999010"
    root.mkdir(parents=True)
    (root / "version").write_text("999010", encoding="utf-8")
    identifiers = {
        "BuildingVariantIds": ["SpacePipe_Forward"],
        "BuildingInternalVariantIds": [],
        "IslandLayoutIds": [],
        "WikiEntryIds": [],
        "ImageIds": [],
        "VideoIds": [],
        "IconIds": [],
    }
    (root / "identifiers.json").write_text(json.dumps(identifiers), encoding="utf-8")
    buildings = [{"Id": "SpacePipe_Forward", "InternalVariants": []}]
    (root / "buildings.json").write_text(json.dumps(buildings), encoding="utf-8")

    rel = import_basedata_bundle(root, replace=False)
    gid = rel.game_identifiers.filter(value="SpacePipe_Forward").first()
    assert gid is not None
    assert gid.sprite_static_relpath == "SpacePipe/SpacePipe_Forward.svg"
