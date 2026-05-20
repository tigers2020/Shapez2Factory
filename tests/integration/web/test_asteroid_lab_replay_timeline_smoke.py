"""Lab product replay timeline SSR smoke (single track, no Optimization Replay panel)."""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from tests.integration.web.test_asteroid_run_solver import _project_slug_via_create

pytestmark = pytest.mark.django_db


def test_lab_template_single_replay_track_nodes() -> None:
    slug = _project_slug_via_create()
    page = Client().get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert page.status_code == 200
    body = page.content.decode()
    assert 'id="lab-replay-frames-data"' in body
    assert 'id="lab-replay-track-metrics-data"' in body
    assert 'id="lab-replay-run-status"' in body
    assert 'id="lab-replay-truncation-hud"' in body
    assert "lab-optimization-replay-data" not in body
    assert "lab-unified-replay-data" not in body
    assert "Optimization Replay" not in body
