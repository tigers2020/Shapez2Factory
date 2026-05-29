"""GZip transport for lab-replay GET (Sequence 13G)."""

from __future__ import annotations

import base64
import gzip
import json
import random

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    """Run Solver and game_data snapshot need pinned import batch."""

    return imported_game_data_batch_module


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(text)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _unique_valid_copy() -> str:
    return _encode_v4_copy(
        {
            "V": random.randint(1, 10_000_000),
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        }
    )


def _lab_replay_url(client: Client) -> str:
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(
        create_url,
        {"copy_code": _unique_valid_copy()},
        HTTP_ACCEPT="application/json",
    )
    assert create_resp.status_code == 200
    slug = json.loads(create_resp.content.decode())["project_slug"]
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    run_body = json.loads(client.post(run_url, HTTP_ACCEPT="application/json").content.decode())
    assert run_body.get("solver_run_id") is not None
    return reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": int(run_body["solver_run_id"])},
    )


def test_lab_replay_get_content_encoding_gzip(client: Client) -> None:
    url = _lab_replay_url(client)
    resp = client.get(url, HTTP_ACCEPT_ENCODING="gzip")
    assert resp.status_code == 200
    assert resp.get("Content-Encoding") == "gzip"
    raw = resp.content
    decoded = gzip.decompress(raw)
    data = json.loads(decoded.decode("utf-8"))
    assert isinstance(data.get("frames"), list)
    assert data.get("frame_count") == len(data["frames"])


def test_lab_replay_get_without_gzip_accept_still_json(client: Client) -> None:
    url = _lab_replay_url(client)
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.get("Content-Encoding") in (None, "")
    data = json.loads(resp.content.decode("utf-8"))
    assert "frames" in data
