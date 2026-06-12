"""Slice 5 harvest paint quarantine audit — v2 isolation + Task 6 cleanup contracts."""

from __future__ import annotations

from pathlib import Path

from tests.support.lab_replay_sprite_wire import NON_SPRITE_OVERLAY_CELL_KINDS

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


def test_harvest_paint_helpers_removed_step_6_6() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "function stageCell(" not in src
    assert "function collectFrameSpatialTargets(" not in src
    assert "function labSpriteRelpathForCell(" not in src
    assert "function applyLabCellSprite(" not in src


def test_python_legacy_harvest_sprite_helpers_removed_step_6_7() -> None:
    from tests.support import lab_replay_sprite_wire as wire

    assert not hasattr(wire, "_legacy_harvest_sprite_entries_for_frame")
    assert not hasattr(wire, "lab_sprite_relpath_for_cell")


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


def test_apply_lab_cell_sprite_from_rel_is_pure_loader_step_6_5() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function applyLabCellSpriteFromRel(", 1)[1].split(
        "function applyLabCellStandaloneSprite(", 1
    )[0]
    assert "clearLabCellSprite" in body
    assert "ensureLabCellSpriteLayer" in body
    assert "labSpriteRelpathForCell" not in body
    assert "resolveSpriteRelForStandaloneOverlayCell" not in body
    assert "isNonSpriteOverlayCell" not in body
    assert "isRouteOverlayCellKind" not in body
    assert "inferTransportSpriteIdentifier" not in body
    assert "overlayCellKind" not in body


def test_render_full_map_uses_direct_rel_loader_step_6_5() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "applyLabCellSpriteFromRel(el, domPlan.spriteRel, domPlan.spriteRotation)" in render_body
    assert "clearLabCellSprite(el)" in render_body
    assert "applyLabCellSprite(" not in render_body
    assert "labSpriteRelpathForCell" not in render_body


def test_standalone_paths_use_resolver_not_full_map_loader_step_6_5() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    diff_body = src.split("function renderDiffOverlays(", 1)[1].split(
        "function renderDecodedCells(", 1
    )[0]
    decoded_body = src.split("function renderDecodedCells(", 1)[1].split(
        "function renderExistingLayoutOverlay(", 1
    )[0]
    existing_body = src.split("function renderExistingLayoutOverlay(", 1)[1].split(
        "function renderCellOverlay(", 1
    )[0]
    connector_body = src.split("function renderPlannedExteriorConnectorHighlights(", 1)[1].split(
        "function clearLabCellSprite(", 1
    )[0]
    for name, body in (
        ("diff", diff_body),
        ("decoded", decoded_body),
        ("existing", existing_body),
        ("connector", connector_body),
    ):
        assert "applyLabCellStandaloneSprite" in body, name
        assert "applyLabCellSpriteFromRel" not in body, name
        assert "applyLabCellSprite(" not in body, name


def test_non_sprite_candidate_miner_removed_step_6_6() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    non_sprite = src.split("var NON_SPRITE_OVERLAY_CELL_KINDS = {", 1)[1].split("};", 1)[0]
    assert "candidate_miner" not in non_sprite
    assert "candidate_transport_stub: true" in non_sprite
    assert "candidate_route_path: true" in non_sprite
    assert "route_path: true" in non_sprite


def test_standalone_resolver_blocks_candidate_miner_step_6_6() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    resolver_body = src.split("function resolveSpriteRelForStandaloneOverlayCell(", 1)[1].split(
        "function attachLabSpriteImgNoDrag(", 1
    )[0]
    assert "isCandidateMinerOverlayKind(ck)" in resolver_body
    assert "return null" in resolver_body.split("isCandidateMinerOverlayKind(ck)", 1)[1][:80]
    assert "isNonSpriteOverlayCell(cell, frame)" in resolver_body
    assert "isRouteOverlayCellKind" in resolver_body


def test_candidate_observation_kind_still_includes_candidate_miner_step_6_6() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function isCandidateObservationOverlayKind(", 1)[1].split(
        "function toneForRouteOverlayKind(", 1
    )[0]
    assert "isCandidateMinerOverlayKind(ck)" in body
    assert "return true" in body.split("isCandidateMinerOverlayKind(ck)", 1)[1][:120]


def test_cell_render_token_has_no_harvest_sprite_step_6_6() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function cellRenderToken(", 1)[1].split("function labPaintTokenForCell(", 1)[
        0
    ]
    assert "labSpriteRelpathForCell" not in body
    assert '"||"' in body


def test_python_non_sprite_mirror_no_candidate_miner_step_6_6() -> None:
    assert "candidate_miner" not in NON_SPRITE_OVERLAY_CELL_KINDS
    assert "candidate_transport_stub" in NON_SPRITE_OVERLAY_CELL_KINDS
    assert "candidate_route_path" in NON_SPRITE_OVERLAY_CELL_KINDS
    assert "route_path" in NON_SPRITE_OVERLAY_CELL_KINDS
