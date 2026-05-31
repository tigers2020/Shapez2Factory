"""Thumbnail sync ??hash skip, regen, clear, failure containment."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.admin_map_list_thumbnail import (
    ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
    canonical_decoded_json_hash,
)
from django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service import (
    clear_admin_list_thumbnail,
    sync_admin_list_thumbnail,
)


@pytest.mark.django_db
def test_sync_creates_thumbnail_and_db_path(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    assert sync_admin_list_thumbnail(reconstructed_row) is True
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name
    assert reconstructed_row.admin_list_thumbnail_hash == canonical_decoded_json_hash(
        dict(reconstructed_row.decoded_json)
    )
    assert (
        reconstructed_row.admin_list_thumbnail_renderer_version
        == ADMIN_LIST_THUMBNAIL_RENDERER_VERSION
    )


@pytest.mark.django_db
def test_sync_skips_when_hash_and_version_match(
    reconstructed_row: m.ReconstructedAsteroidMap,
) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    reconstructed_row.refresh_from_db()
    name_before = reconstructed_row.admin_list_thumbnail.name
    assert sync_admin_list_thumbnail(reconstructed_row) is False
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name == name_before


@pytest.mark.django_db
def test_sync_with_force_regenerates(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    reconstructed_row.refresh_from_db()
    assert sync_admin_list_thumbnail(reconstructed_row, force=True) is True
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name
    assert reconstructed_row.admin_list_thumbnail_hash


@pytest.mark.django_db
def test_clear_removes_thumbnail_fields(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    clear_admin_list_thumbnail(int(reconstructed_row.pk))
    reconstructed_row.refresh_from_db()
    assert not reconstructed_row.admin_list_thumbnail
    assert reconstructed_row.admin_list_thumbnail_hash == ""


@pytest.mark.django_db
def test_sync_render_failure_clears_and_does_not_raise(
    reconstructed_row: m.ReconstructedAsteroidMap,
) -> None:
    with patch(
        "django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service.render_list_thumbnail_image_bytes",
        side_effect=ValueError("render failed"),
    ):
        assert sync_admin_list_thumbnail(reconstructed_row) is True
    reconstructed_row.refresh_from_db()
    assert not reconstructed_row.admin_list_thumbnail


@pytest.mark.django_db
def test_regenerate_command_by_pk(reconstructed_row: m.ReconstructedAsteroidMap) -> None:
    from django.core.management import call_command

    clear_admin_list_thumbnail(int(reconstructed_row.pk))
    call_command(
        "regenerate_reconstructed_map_thumbnails",
        pk=[int(reconstructed_row.pk)],
        force=True,
    )
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name
