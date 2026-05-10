"""Smoke: asteroid optimizer page exposes wired API URLs from view context."""

from django.test import Client
from django.urls import reverse


def test_asteroid_optimizer_page_get_includes_copy_preview_url() -> None:
    url = reverse("web:asteroid")
    expected_preview = reverse("shapez_asteroid:copy_preview")
    response = Client().get(url)

    assert response.status_code == 200
    assert expected_preview.encode() in response.content
