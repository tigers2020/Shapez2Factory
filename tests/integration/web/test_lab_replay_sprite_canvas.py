"""Browser smoke: replay sprite canvas paints transport belts (Playwright)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from django.test import Client, override_settings
from django.urls import reverse

REPO = Path(__file__).resolve().parents[3]
PLAYWRIGHT_SCRIPT = REPO / "scripts" / "test_lab_replay_sprite_canvas.mjs"

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    return imported_game_data_batch_module


def _unique_valid_copy() -> str:
    import base64
    import gzip
    import random

    root = {
        "V": random.randint(1, 10_000_000),
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    return f"SHAPEZ2-4-{base64.b64encode(gzip.compress(text)).decode('ascii')}"


def _lab_page_url_after_solver(client: Client, live_server) -> str:
    create_resp = client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": _unique_valid_copy()},
        HTTP_ACCEPT="application/json",
    )
    assert create_resp.status_code == 200
    slug = json.loads(create_resp.content.decode())["project_slug"]
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    run_resp = client.post(run_url, HTTP_ACCEPT="application/json")
    assert run_resp.status_code == 200
    body = json.loads(run_resp.content.decode())
    assert body.get("ok") is True
    frames = body.get("lab_replay_frames_json")
    assert isinstance(frames, list) and frames
    page_path = reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug})
    return f"{live_server.url}{page_path}"


def _playwright_chromium_ready() -> bool:
    try:
        proc = subprocess.run(
            ["node", "-e", "import('playwright').then(p=>p.chromium.launch().then(b=>b.close()))"],
            cwd=str(REPO),
            capture_output=True,
            timeout=60,
            check=False,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@pytest.mark.skipif(not PLAYWRIGHT_SCRIPT.is_file(), reason="playwright script missing")
@pytest.mark.skipif(not _playwright_chromium_ready(), reason="playwright chromium not installed")
@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_lab_replay_sprite_canvas_paints_transport_tiles(client: Client, live_server) -> None:
    node = "node"
    if sys.platform == "win32":
        node = "node.exe"
    lab_url = _lab_page_url_after_solver(client, live_server)
    proc = subprocess.run(
        [node, str(PLAYWRIGHT_SCRIPT), lab_url],
        cwd=str(REPO),
        capture_output=True,
        timeout=180,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        msg = stderr or stdout or f"exit {proc.returncode}"
        pytest.fail(f"playwright sprite canvas smoke failed: {msg}")
