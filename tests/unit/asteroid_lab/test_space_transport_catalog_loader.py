"""DB-first space transport catalog loader policy."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.services.space_transport_catalog_loader import (
    SpaceTransportCatalogLoadSource,
    SpaceTransportCatalogUnavailable,
    clear_space_transport_catalog_loader_cache,
    get_last_space_transport_catalog_load_source,
    load_space_transport_catalog,
    try_load_space_transport_catalog_from_snapshot,
)
from django_apps.game_data.models import SpaceTransportLayoutRegistry

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GAME_DATA = _REPO_ROOT / "documents" / "knowledge" / "raw" / "game_data"


@pytest.fixture(autouse=True)
def _clear_loader_cache() -> None:
    clear_space_transport_catalog_loader_cache()
    yield
    clear_space_transport_catalog_loader_cache()


@pytest.mark.django_db
def test_loader_uses_db_when_registry_populated() -> None:
    if SpaceTransportLayoutRegistry.objects.count() < 54:
        if not (_GAME_DATA / "manifest.json").is_file():
            pytest.skip("game_data bundle not present")
        from django.core.management import call_command

        call_command("import_game_data", source=str(_GAME_DATA), batch_name="loader-db-test")

    with patch(
        "django_apps.asteroid_lab.services.space_transport_catalog_loader._load_catalog_from_json",
    ) as json_loader:
        catalog = load_space_transport_catalog(prefer_db=True)

    json_loader.assert_not_called()
    assert catalog.lookup_tile_id("SpaceBelt_Forward").transport_kind == "space_belt"
    assert (
        get_last_space_transport_catalog_load_source() == SpaceTransportCatalogLoadSource.DB.value
    )


@pytest.mark.django_db
def test_loader_json_fallback_when_db_empty(caplog: pytest.LogCaptureFixture) -> None:
    if not (_GAME_DATA / "research_unlocks.json").is_file():
        pytest.skip("game_data JSON not present")

    SpaceTransportLayoutRegistry.objects.all().delete()

    catalog = load_space_transport_catalog(prefer_db=True)

    assert catalog.lookup_tile_id("SpacePipe_Forward").transport_kind == "space_pipe"
    assert get_last_space_transport_catalog_load_source() == (
        SpaceTransportCatalogLoadSource.JSON_FALLBACK.value
    )
    assert any("space_transport_catalog_json_fallback" in rec.message for rec in caplog.records)


@pytest.mark.django_db
def test_loader_hard_fails_when_db_and_json_missing() -> None:
    SpaceTransportLayoutRegistry.objects.all().delete()

    with patch(
        "django_apps.asteroid_lab.services.space_transport_catalog_loader._resolve_json_source_dir",
        return_value=None,
    ):
        with pytest.raises(SpaceTransportCatalogUnavailable):
            load_space_transport_catalog(prefer_db=True)


@pytest.mark.django_db
def test_loader_builds_catalog_from_snapshot_layouts() -> None:
    if SpaceTransportLayoutRegistry.objects.count() < 54:
        if not (_GAME_DATA / "manifest.json").is_file():
            pytest.skip("game_data bundle not present")
        from django.core.management import call_command

        call_command("import_game_data", source=str(_GAME_DATA), batch_name="loader-snapshot-test")

    from django_apps.game_data.services.game_data_snapshot_export import (
        build_game_data_snapshot_payload,
    )

    payload = build_game_data_snapshot_payload()
    SpaceTransportLayoutRegistry.objects.all().delete()

    catalog = try_load_space_transport_catalog_from_snapshot(payload)
    assert catalog is not None
    assert catalog.lookup_tile_id("SpaceBelt_LeftTurn").transport_kind == "space_belt"
