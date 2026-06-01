"""ReconstructedAsteroidMap admin changelist ??thumbnail img, actions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.admin import ReconstructedAsteroidMapAdmin
from django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service import (
    clear_admin_list_thumbnail,
    sync_admin_list_thumbnail,
)


@pytest.mark.django_db
def test_save_model_syncs_thumbnail_when_missing(
    reconstructed_row: m.ReconstructedAsteroidMap,
    rf: object,
) -> None:
    assert not reconstructed_row.admin_list_thumbnail
    site = AdminSite()
    model_admin = ReconstructedAsteroidMapAdmin(m.ReconstructedAsteroidMap, site)
    request = rf.post("/")
    model_admin.save_model(request, reconstructed_row, MagicMock(), change=True)
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name


@pytest.mark.django_db
def test_changelist_renders_without_thumbnail_placeholder(
    staff_client: Client,
    reconstructed_row: m.ReconstructedAsteroidMap,
) -> None:
    url = reverse("admin:asteroid_lab_reconstructedasteroidmap_changelist")
    response = staff_client.get(url)
    assert response.status_code == 200
    assert "no thumbnail" in response.content.decode()


@pytest.mark.django_db
def test_changelist_uses_img_not_mini_map_grid(
    staff_client: Client,
    reconstructed_row: m.ReconstructedAsteroidMap,
) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    url = reverse("admin:asteroid_lab_reconstructedasteroidmap_changelist")
    response = staff_client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    assert "genetic-sample-mini-map-cell" not in html
    assert "<img" in html


@pytest.mark.django_db
def test_admin_regenerate_action_smoke(
    staff_client: Client,
    reconstructed_row: m.ReconstructedAsteroidMap,
) -> None:
    clear_admin_list_thumbnail(int(reconstructed_row.pk))
    changelist = reverse("admin:asteroid_lab_reconstructedasteroidmap_changelist")
    response = staff_client.post(
        changelist,
        {
            "action": "regenerate_admin_list_thumbnails",
            "select_across": "0",
            "_selected_action": [str(reconstructed_row.pk)],
        },
    )
    assert response.status_code == 302
    reconstructed_row.refresh_from_db()
    assert reconstructed_row.admin_list_thumbnail.name


@pytest.mark.django_db
def test_admin_clear_action_smoke(
    staff_client: Client,
    reconstructed_row: m.ReconstructedAsteroidMap,
) -> None:
    sync_admin_list_thumbnail(reconstructed_row)
    changelist = reverse("admin:asteroid_lab_reconstructedasteroidmap_changelist")
    response = staff_client.post(
        changelist,
        {
            "action": "clear_admin_list_thumbnails",
            "select_across": "0",
            "_selected_action": [str(reconstructed_row.pk)],
        },
    )
    assert response.status_code == 302
    reconstructed_row.refresh_from_db()
    assert not reconstructed_row.admin_list_thumbnail
