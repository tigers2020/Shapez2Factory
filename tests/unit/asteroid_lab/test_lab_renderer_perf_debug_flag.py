"""Reserve data-lab-perf-debug hook name for RENDER-1/3 touched-cell counters."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_renderer_perf_debug_flag_reserved() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "data-lab-perf-debug" in src
    assert "labPerfDebugEnabled" in src
    assert "[lab-perf] touched_cells" in src
