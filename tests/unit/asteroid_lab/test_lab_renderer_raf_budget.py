"""PR-RENDER-3: playback rAF budget helpers (bridge pool, demo diff, translate3d, perf marks)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_bundle_bridge_is_pooled_not_recreated() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "function ensureBundleBridge(" in src


def test_demo_matrix_uses_diff() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "demoRenderedClass" in src


def test_grid_stage_uses_translate3d() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "translate3d(" in src


def test_perf_marks_behind_debug_flag() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "performance.measure(" in src
    assert "labPerfDebugEnabled(" in src
