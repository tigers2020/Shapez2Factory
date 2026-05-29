"""Lab lazy replay must refresh track metrics (frozen exterior plan)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_apply_loaded_lab_replay_payload_assigns_replay_track_metrics() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "function applyLoadedLabReplayPayload(payload)" in js
    assert "payload.replay_track_metrics" in js
    assert "replayTrackMetrics = payload.replay_track_metrics" in js


def test_lazy_replace_lab_replay_payload_applies_track_metrics_before_early_return() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    idx_lazy = js.find('lazy.mode === "lazy"')
    assert idx_lazy >= 0
    chunk = js[idx_lazy : idx_lazy + 1200]
    assert "replay_track_metrics" in chunk
