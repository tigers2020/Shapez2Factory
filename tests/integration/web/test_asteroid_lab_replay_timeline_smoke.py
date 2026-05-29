"""Lab product replay timeline SSR smoke (single track, no Optimization Replay panel)."""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from tests.integration.web.test_lab_replay_ssr_manifest import (
    _project_page_html,
    _unique_valid_copy,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    """Run Solver needs pinned game_data import batch."""

    return imported_game_data_batch_module


def test_lab_template_single_replay_track_nodes(client: Client) -> None:
    """Lazy SSR: manifest embed after solve; metrics live inside manifest JSON."""

    body, _proj = _project_page_html(
        client,
        _unique_valid_copy(),
        with_solver_run=True,
    )
    assert 'id="lab-replay-manifest-data"' in body
    assert 'id="lab-replay-frames-data"' not in body
    assert 'id="lab-replay-track-metrics-data"' not in body
    assert 'id="lab-replay-run-status"' in body
    assert 'id="lab-replay-truncation-hud"' in body
    assert "lab-optimization-replay-data" not in body
    assert "lab-unified-replay-data" not in body
    assert "Optimization Replay" not in body
