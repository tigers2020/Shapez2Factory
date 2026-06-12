"""Slice 5 harvest paint quarantine audit — v2 isolation + deprecation markers."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
LAB_JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_build_canvas_paint_plan_v2_has_no_stage_cell() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    fn = src.split("function buildCanvasPaintPlan(", 1)[1]
    v2_region = fn.split("labPaintV2Enabled()", 1)[1]
    legacy_start = v2_region.find("const overlays = []")
    assert legacy_start >= 0
    assert "stageCell" not in v2_region[:legacy_start]
    assert "collectFrameSpatialTargets" not in v2_region[:legacy_start]


def test_legacy_canvas_harvest_still_present_when_flag_off() -> None:
    """Policy (A): legacy harvest branch retained until Slice 5 Task 6 HITL delete."""
    src = LAB_JS.read_text(encoding="utf-8")
    fn = src.split("function buildCanvasPaintPlan(", 1)[1]
    assert "const overlays = []" in fn
    legacy = fn.split("const overlays = []", 1)[1]
    assert "function stageCell(" in legacy
    assert "collectFrameSpatialTargets" in legacy
    assert "labSpriteRelpathForCell" in legacy


def test_harvest_functions_marked_deprecated() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    for name in (
        "function collectFrameSpatialTargets(",
        "function labSpriteRelpathForCell(",
        "function frameCellIndexMap(",
        "function stageCell(",
    ):
        idx = src.find(name)
        assert idx >= 0, f"missing {name}"
        window = src[max(0, idx - 400) : idx]
        assert (
            "HARVEST" in window or "deprecated" in window.lower() or "@deprecated" in window
        ), f"{name} lacks quarantine marker within 400 chars"


def test_frame_cell_index_map_v2_delegates_to_paint_plan() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function frameCellIndexMap(", 1)[1].split(
        "function resetDomCellsAtIndicesForFrame(", 1
    )[0]
    assert "labPaintV2Enabled()" in body
    assert "buildCellByGridIndexFromFrame" in body
    assert "collectFrameSpatialTargets" in body


def test_v2_dom_path_does_not_use_lab_sprite_relpath_for_cell() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "if (domPlan)" in render_body
    dom_block = render_body.split("if (domPlan)", 1)[1]
    next_legacy = dom_block.find("let tone = toneForFullMapCell")
    dom_v2 = dom_block[:next_legacy] if next_legacy >= 0 else dom_block[:1200]
    assert "labSpriteRelpathForCell" not in dom_v2
