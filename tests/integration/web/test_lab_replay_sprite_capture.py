"""Playwright screenshot capture for Lab replay sprites (manual evidence)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from tests.integration.web.test_lab_replay_sprite_canvas import (
    PLAYWRIGHT_SCRIPT,
    REPO,
    _lab_page_url_after_solver,
    _playwright_chromium_ready,
    _unique_valid_copy,
)

pytestmark = pytest.mark.django_db

CAPTURE_SCRIPT = REPO / "scripts" / "capture_lab_replay_sprite_screenshot.mjs"
OUT_DIR = REPO / "var" / "log" / "lab_replay_sprite_capture"


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    return imported_game_data_batch_module


@pytest.mark.skipif(not CAPTURE_SCRIPT.is_file(), reason="capture script missing")
@pytest.mark.skipif(not _playwright_chromium_ready(), reason="playwright chromium not installed")
@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_capture_lab_replay_sprite_screenshots(client: Client, live_server) -> None:
    lab_url = _lab_page_url_after_solver(client, live_server)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    node = "node.exe" if sys.platform == "win32" else "node"
    proc = subprocess.run(
        [node, str(CAPTURE_SCRIPT), lab_url, str(OUT_DIR)],
        cwd=str(REPO),
        capture_output=True,
        timeout=180,
        check=False,
    )
    stdout = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
    stderr = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
    assert proc.returncode == 0, stderr or stdout or f"exit {proc.returncode}"
    result = json.loads(stdout.splitlines()[-1])
    assert result.get("ok") is True
    assert int(result.get("opaquePixels", 0)) > 0
    pngs = sorted(OUT_DIR.glob("lab_replay_sprite_*_sprite_canvas.png"))
    assert pngs, f"no sprite canvas png in {OUT_DIR}"
    print(f"CAPTURED_SPRITE_PNG={pngs[-1]}")
