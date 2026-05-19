"""Lab optimization replay HUD template + dual-track wiring (PR9)."""

from __future__ import annotations

import json
import re

import pytest
from django.test import Client
from django.urls import reverse

from tests.integration.web.test_asteroid_run_solver import _project_slug_via_create

pytestmark = pytest.mark.django_db


def _optimization_replay_from_page_html(html: bytes) -> dict:
    text = html.decode()
    m = re.search(
        r'<script[^>]+id="lab-optimization-replay-data"[^>]*>(.*?)</script>',
        text,
        re.DOTALL,
    )
    assert m is not None, "lab-optimization-replay-data json_script missing"
    return json.loads(m.group(1))


def test_lab_template_includes_optimization_replay_hud_nodes() -> None:
    slug = _project_slug_via_create()
    page = Client().get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert page.status_code == 200
    body = page.content.decode()
    for node_id in (
        "lab-optimization-replay-status",
        "lab-optimization-replay-truncation",
        "lab-optimization-replay-diagnostic",
        "lab-optimization-replay-run",
    ):
        assert f'id="{node_id}"' in body
    assert "data-lab-run-solver-url" in body
    assert f"/asteroid-miner-layout/p/{slug}/run-solver/" in body
