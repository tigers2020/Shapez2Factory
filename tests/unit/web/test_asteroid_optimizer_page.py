"""Smoke: asteroid optimizer page exposes wired API URLs from view context."""

from django.test import Client
from django.urls import reverse


def test_asteroid_optimizer_page_get_includes_copy_preview_url() -> None:
    url = reverse("web:asteroid")
    expected_preview = reverse("shapez_asteroid:copy_preview")
    response = Client().get(url)

    assert response.status_code == 200
    assert expected_preview.encode() in response.content
    assert b"data-am-solver-replay-meta" in response.content


def test_asteroid_optimizer_recovery_overlay_meta_smoke() -> None:
    """STEP10 replay SVG overlay group class is wired in the optimizer template."""

    response = Client().get(reverse("web:asteroid"))
    assert response.status_code == 200
    assert b"am-step10-replay-overlay" in response.content
    assert b"data-msg-route-replay-removed" in response.content
    assert b"am-route-replay-cells-overlay" in response.content
    assert b"normalizeReplayTransportKind" in response.content


def test_asteroid_optimizer_map_cells_fetch_cache_smoke() -> None:
    """Map-cells GET is memoized per bbox in inline script (replay must not spam server)."""

    response = Client().get(reverse("web:asteroid"))
    assert response.status_code == 200
    assert b"fetchMapCellsBboxOnce" in response.content
    assert b"clearMapCellsFetchCache" in response.content
