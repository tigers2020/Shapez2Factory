"""Unit tests for ``asteroid_sprite_projection`` (Phase A Task 5)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from django_apps.asteroid_lab.catalog.asteroid_sprite_projection import resolve_sprite_ref
from django_apps.asteroid_lab.catalog.projection_source import ProjectionSourceKind
from django_apps.game_data.models import AssetMetaReference, GameContentAsset, ImportBatch


def _make_import_batch(*, suffix: str) -> ImportBatch:
    return ImportBatch.objects.create(
        batch_name=f"sprite-projection-{suffix}",
        manifest_self_hash=f"sha256:sprite-projection-{suffix}",
        game_version="test",
        unity_version="u",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )


@pytest.mark.django_db
def test_resolve_sprite_ref_meta_and_content_asset_returns_game_data_canon() -> None:
    batch = _make_import_batch(suffix="canon")
    asset = GameContentAsset.objects.create(
        canonical_id="sprite:layout-shape-miner",
        import_batch=batch,
        content_kind=GameContentAsset.ContentKind.SPRITE,
        source_stable_id="stable-sprite-1",
        content_path="sprites/layout_shape_miner.png",
        logical_path="Layout_ShapeMiner",
        display_name_key="Layout_ShapeMiner",
        dump_source_type="sprite",
        source_row_index=0,
    )
    AssetMetaReference.objects.create(
        canonical_id="meta:layout-shape-miner",
        import_batch=batch,
        meta_stable_id="meta-stable-1",
        content_asset=asset,
        logical_path="Layout_ShapeMiner",
        display_name_key="Layout_ShapeMiner",
        source_row_index=0,
    )

    ref = resolve_sprite_ref("Layout_ShapeMiner", import_batch_id=int(batch.pk))

    assert ref.source_kind is ProjectionSourceKind.GAME_DATA_CANON
    assert ref.sprite_path == "Layout_ShapeMiner"
    assert ref.canonical_id == "meta:layout-shape-miner"
    assert ref.source_detail.startswith("game_data:asset_meta_reference:")


@pytest.mark.django_db
def test_resolve_sprite_ref_import_batch_id_filters_lookup() -> None:
    batch_a = _make_import_batch(suffix="a")
    batch_b = _make_import_batch(suffix="b")
    asset_a = GameContentAsset.objects.create(
        canonical_id="sprite:a:layout",
        import_batch=batch_a,
        content_kind=GameContentAsset.ContentKind.SPRITE,
        source_stable_id="stable-a",
        content_path="sprites/a.png",
        logical_path="Layout_TestBatchA",
        source_row_index=0,
    )
    GameContentAsset.objects.create(
        canonical_id="sprite:b:layout",
        import_batch=batch_b,
        content_kind=GameContentAsset.ContentKind.SPRITE,
        source_stable_id="stable-b",
        content_path="sprites/b.png",
        logical_path="Layout_TestBatchA",
        source_row_index=0,
    )

    ref = resolve_sprite_ref("Layout_TestBatchA", import_batch_id=int(batch_a.pk))

    assert ref.source_kind is ProjectionSourceKind.GAME_DATA_CANON
    assert ref.canonical_id == asset_a.canonical_id


@pytest.mark.django_db
def test_resolve_sprite_ref_content_path_fallback_when_logical_path_empty() -> None:
    batch = _make_import_batch(suffix="content-path")
    GameContentAsset.objects.create(
        canonical_id="sprite:content-path-only",
        import_batch=batch,
        content_kind=GameContentAsset.ContentKind.SPRITE,
        source_stable_id="stable-cp",
        content_path="Layout_ContentPathOnly",
        logical_path="",
        source_row_index=0,
    )

    ref = resolve_sprite_ref("Layout_ContentPathOnly", import_batch_id=int(batch.pk))

    assert ref.source_kind is ProjectionSourceKind.GAME_DATA_CANON
    assert ref.sprite_path == "Layout_ContentPathOnly"
    assert "content_path" in ref.source_detail


@pytest.mark.django_db
def test_resolve_sprite_ref_unknown_space_belt_uses_temporary_compat() -> None:
    ref = resolve_sprite_ref("SpaceBelt_Forward", import_batch_id=999_999)

    assert ref.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT
    assert ref.layout_t == "SpaceBelt_Forward"
    assert ref.canonical_id is None
    assert ref.source_detail.startswith("compat:")
