"""Guard R5: rAF playback scheduler must stop when paused (static source contract)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_set_playing_false_stops_raf_scheduler() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "function stopPlaybackScheduler()" in src
    assert "cancelAnimationFrame" in src
    idx = src.find("function setPlaying(")
    assert idx >= 0
    body = src[idx : idx + 800]
    assert "stopPlaybackScheduler()" in body


def test_tick_playback_returns_when_not_playing() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function tickPlayback(")
    assert idx >= 0
    body = src[idx : idx + 200]
    assert "if (!isPlaying)" in body
