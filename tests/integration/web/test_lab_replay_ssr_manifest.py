"""SSR manifest-only replay embed (Sequence 13D-SSR)."""

from __future__ import annotations

import base64
import gzip
import json
import random

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    """Run Solver and game_data snapshot need pinned import batch."""

    return imported_game_data_batch_module


# Calibrate after first green run on CI fixture (same policy as LAB_REPLAY_LAZY_POST_MAX_BYTES).
LAB_REPLAY_SSR_DOCUMENT_MAX_BYTES = 512_000
# Single preview frame + manifest metadata; not 80+ timeline frames.
LAB_REPLAY_SSR_MAX_FRAME_INDEX_MARKERS = 24


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


def _project_page_html(
    client: Client,
    copy_code: str,
    *,
    with_solver_run: bool = False,
) -> tuple[str, m.AsteroidProject]:
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(
        create_url,
        {"copy_code": copy_code},
        HTTP_ACCEPT="application/json",
    )
    assert create_resp.status_code == 200
    slug = json.loads(create_resp.content.decode())["project_slug"]
    proj = m.AsteroidProject.objects.get(slug=slug)
    if with_solver_run:
        run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
        run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
        assert run_resp.status_code == 200
    page = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert page.status_code == 200
    return page.content.decode(), proj


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_has_manifest_not_frames_script(client: Client) -> None:
    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert 'id="lab-replay-manifest-data"' in html
    assert 'id="lab-replay-frames-data"' not in html
    assert 'id="lab-initial-replay-frame-data"' not in html
    assert 'id="lab-replay-track-metrics-data"' not in html


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_document_bytes_under_cap(client: Client) -> None:
    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert len(html.encode("utf-8")) <= LAB_REPLAY_SSR_DOCUMENT_MAX_BYTES


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_no_bulk_timeline_markers(client: Client) -> None:
    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert html.count('"frame_index"') <= LAB_REPLAY_SSR_MAX_FRAME_INDEX_MARKERS


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_ssr_manifest_fetch_url_matches_latest_run(client: Client) -> None:
    html, proj = _project_page_html(client, _unique_valid_copy(), with_solver_run=True)
    latest_run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert latest_run is not None
    marker = 'id="lab-replay-manifest-data"'
    start = html.index(marker)
    end = html.index("</script>", start)
    blob = html[start:end]
    assert f"/solver-runs/{latest_run.pk}/lab-replay/" in blob


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_project_page_inline_ssr_keeps_replay_track_metrics_for_truncation_hud(
    client: Client,
) -> None:
    """Inline rollback: legacy frames + separate metrics for updateReplayTruncationHud."""

    html, _proj = _project_page_html(client, _unique_valid_copy())
    assert 'id="lab-replay-frames-data"' in html
    assert 'id="lab-replay-track-metrics-data"' in html
    assert 'id="lab-replay-manifest-data"' not in html
    assert 'id="lab-initial-replay-frame-data"' not in html
