"""PR-RENDER-2: layout read/write split — cache present; no layout read in applyFrame."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_layout_cache_present() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "labLayoutCache" in src
    assert "function refreshLabLayoutCache(" in src


def test_apply_frame_does_not_read_offset_width() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function applyFrame(")
    assert idx >= 0
    end = src.find("function setPlaying(", idx)
    body = src[idx:end] if end > idx else src[idx : idx + 4000]
    assert "offsetWidth" not in body
    assert "getBoundingClientRect" not in body
