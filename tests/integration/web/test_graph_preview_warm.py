"""Staff graph-preview warm API (validation; full Playwright not required)."""

from __future__ import annotations

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from django_apps.shapez_solver.view_graph_serialization import build_preview_scene
from django_apps.web.services.graph_preview import PlaywrightPngGraphPreviewRenderer


@pytest.mark.django_db
def test_graph_preview_warm_requires_staff() -> None:
    url = reverse("web:macro-pattern-staff-api-graph-preview-warm")
    scene = build_preview_scene("CuCuCuCu")
    ck = PlaywrightPngGraphPreviewRenderer().cache_key(scene)
    resp = Client().post(
        url,
        data=json.dumps({"cache_key": ck, "preview_scene": scene}),
        content_type="application/json",
    )
    assert resp.status_code == 302


@pytest.mark.django_db
def test_graph_preview_warm_rejects_cache_key_mismatch() -> None:
    User = get_user_model()
    user = User.objects.create_user("warm_staff", password="secret", is_staff=True)
    client = Client()
    client.force_login(user)
    url = reverse("web:macro-pattern-staff-api-graph-preview-warm")
    scene = build_preview_scene("CuCuCuCu")
    resp = client.post(
        url,
        data=json.dumps({"cache_key": "notavalidhexcachekey12", "preview_scene": scene}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("ok") is False
