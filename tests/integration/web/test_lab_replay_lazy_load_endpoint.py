"""GET lab-replay lazy-load endpoint (Sequence 13C)."""

from __future__ import annotations

import json

import pytest
from django.test import Client, override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    """Run Solver view builds game_data snapshot from pinned import batch."""

    return imported_game_data_batch_module


def _create_project_and_run(client: Client) -> tuple[str, int]:
    from tests.integration.web.test_asteroid_miner_layout_solver import (
        _unique_valid_copy,
    )

    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy_code}, HTTP_ACCEPT="application/json")
    data = json.loads(create_resp.content.decode())
    slug = str(data["project_slug"])
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
    body = json.loads(run_resp.content.decode())
    return slug, int(body["solver_run_id"])


def test_lab_replay_get_returns_frames_for_run(client: Client) -> None:
    slug, run_id = _create_project_and_run(client)
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": run_id},
    )
    resp = client.get(url, HTTP_ACCEPT="application/json")
    assert resp.status_code == 200
    payload = json.loads(resp.content.decode())
    assert payload["run_id"] == run_id
    assert payload["frame_count"] == len(payload["frames"])
    assert payload["frame_count"] >= 1


def test_lab_replay_get_unknown_run_returns_404(client: Client) -> None:
    slug, _run_id = _create_project_and_run(client)
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": 9_999_999},
    )
    resp = client.get(url, HTTP_ACCEPT="application/json")
    assert resp.status_code == 404


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_lab_replay_get_matches_inline_post_for_same_run(client: Client) -> None:
    from tests.integration.web.test_asteroid_miner_layout_solver import _unique_valid_copy

    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy_code}, HTTP_ACCEPT="application/json")
    data = json.loads(create_resp.content.decode())
    slug = str(data["project_slug"])
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    post_body = json.loads(client.post(run_url, HTTP_ACCEPT="application/json").content.decode())
    run_id = int(post_body["solver_run_id"])
    inline_frames = list(post_body["lab_replay_frames_json"])

    get_url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": run_id},
    )
    get_body = json.loads(client.get(get_url, HTTP_ACCEPT="application/json").content.decode())
    assert get_body["frames"] == inline_frames
