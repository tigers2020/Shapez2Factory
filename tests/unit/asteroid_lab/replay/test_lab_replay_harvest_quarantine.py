"""Slice 5 harvest paint quarantine audit — v2 isolation + deprecation markers."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
LAB_JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_build_canvas_paint_plan_delegates_to_paint_plan_only() -> None:
    """Task 6.3: canvas paint always uses LabReplayPaintPlan; no legacy harvest."""
    src = LAB_JS.read_text(encoding="utf-8")
    fn = src.split("function buildCanvasPaintPlan(", 1)[1].split(
        "function refreshLabCanvasAfterLayoutChange(", 1
    )[0]
    assert "LabReplayPaintPlan.buildLabPaintPlanFromFrame" in fn
    assert "labPaintV2Enabled()" not in fn
    assert "stageCell" not in fn
    assert "collectFrameSpatialTargets" not in fn
    assert "collectReplaySpatialCoordsForLayout" not in fn
    assert "const overlays = []" not in fn


def test_harvest_sprite_helper_still_quarantined() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    idx = src.find("function labSpriteRelpathForCell(")
    assert idx >= 0
    window = src[max(0, idx - 400) : idx]
    assert (
        "HARVEST" in window or "deprecated" in window.lower() or "@deprecated" in window
    )
    assert "function stageCell(" not in src
    assert "function collectFrameSpatialTargets(" not in src


def test_frame_cell_index_map_always_delegates_to_paint_plan() -> None:
    """Task 6.4: frameCellIndexMap always uses paint-plan index; no harvest fallback."""
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function frameCellIndexMap(", 1)[1].split(
        "function resetDomCellsAtIndicesForFrame(", 1
    )[0]
    assert "labPaintV2Enabled()" not in body
    assert "buildCellByGridIndexFromFrame" in body
    assert "collectFrameSpatialTargets" not in body
    assert "collectReplaySpatialCoordsForLayout" not in body


def test_spatial_layout_helper_is_coord_only_not_paint() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function collectReplaySpatialCoordsForLayout(", 1)[1].split(
        "function collectReplayFrameCellIndices(", 1
    )[0]
    assert "fullMapCellsFromFrame(frame)" in body
    assert "labCellsFromMapView(mapView)" in body
    assert "overlayCellsFromMapView(mapView)" in body
    assert "cellDeltaCellsFromMapView(mapView)" in body
    assert "collectDiffPaintTargets(frame)" in body
    assert "collectOverlayPaintTargets(overlayJson)" in body
    assert "labSpriteRelpathForCell" not in body


def test_v2_dom_path_does_not_use_lab_sprite_relpath_for_cell() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "labSpriteRelpathForCell" not in render_body
    assert "createDomPlanResolverForFrame" in render_body
    assert "if (!domPlan)" in render_body


def test_replay_full_map_dom_legacy_branch_removed_step_6_4() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "candidateObservationToneClasses" not in render_body
    assert "isNonSpriteOverlayCell(cell, frame)" not in render_body
    assert "if (!candidateObs)" not in render_body
