"""PR-RENDER-5: canvas overlay + sprite renderer contracts."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS_DIR = REPO / "django_apps" / "web" / "static" / "web" / "js"
TPL = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
LAB_JS = JS_DIR / "asteroid_miner_layout_lab.js"
SANITIZE_JS = JS_DIR / "lab_replay_wire_sanitize.js"
HEIGHT_JS = JS_DIR / "lab_replay_height_layer.js"
OVERLAY_REGISTRY_JS = JS_DIR / "lab_replay_overlay_bucket_registry.js"
PAINT_JS = JS_DIR / "lab_replay_paint_plan.js"
EFFECTIVE_CELL_JS = JS_DIR / "lab_effective_cell_view.js"


def test_canvas_renderer_module_contract() -> None:
    src = (JS_DIR / "lab_replay_canvas_renderer.js").read_text(encoding="utf-8")
    assert "createLabCanvasRenderer" in src
    assert "drawFrame" in src
    assert "hitTest" in src
    assert "preloadSprites" in src
    assert "spriteDrawGeneration" in src
    assert "redrawSpriteLayer" in src
    assert "overlayFillForKind" in src
    assert "let layout = opts.layout" in src
    assert "const layout = opts.layout" not in src
    assert "viewportScale" in src
    assert "devicePixelRatio" in src


def test_canvas_viewport_zoom_backing_store_contract() -> None:
    terrain = (JS_DIR / "lab_replay_canvas_terrain.js").read_text(encoding="utf-8")
    lab = LAB_JS.read_text(encoding="utf-8-sig")
    assert "viewportScale" in terrain
    assert "labReplayViewportZoom" in lab
    assert "labCanvasBackingViewportScale" in lab
    assert "LAB_CANVAS_VIEWPORT_SCALE_MAX = LAB_VIEWPORT_MAX_SCALE" in lab
    assert "LAB_CANVAS_ZOOM_SETTLE_MS" in lab
    assert "scheduleLabCanvasZoomRefresh" in lab
    wheel_block = lab.split("function handleLabViewportWheel(", 1)[1].split(
        "function labPointerShouldStartViewportPan", 1
    )[0]
    assert "scheduleLabCanvasZoomRefresh" in wheel_block
    assert "refreshLabCanvasAfterLayoutChange" not in wheel_block
    settle_block = lab.split("function scheduleLabCanvasZoomRefresh(", 1)[1].split(
        "function labCanvasViewportScale", 1
    )[0]
    assert "LAB_CANVAS_ZOOM_SETTLE_MS" in settle_block
    assert "refreshLabCanvasAfterLayoutChange" in settle_block
    assert "labReplayViewportZoom = zoom" in lab


def test_template_has_overlay_and_sprite_canvases() -> None:
    tpl = TPL.read_text(encoding="utf-8")
    assert 'id="lab-replay-overlay-canvas"' in tpl
    assert 'id="lab-replay-sprite-canvas"' in tpl
    assert "lab_replay_canvas_renderer.js" in tpl


def test_lab_js_wires_canvas_renderer() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "function labCanvasRendererEnabled(" in src
    assert "function mountLabCanvasRenderer(" in src
    assert "function buildCanvasPaintPlan(" in src
    assert "function warmupLabReplaySpriteCache(" in src
    assert "function applyLabCanvasServerReplayFrame(" in src
    assert "lab-replay-canvas-hit-layer" in src
    let_pos = src.index("let labCanvasRenderer = null")
    surface_pos = src.index("function initializeServerReplaySurface(")
    mount_call = src.index("mountLabCanvasRenderer();", surface_pos)
    assert let_pos != -1 and let_pos < surface_pos
    assert mount_call > src.index("labSpriteBaseUrl =", surface_pos)
    apply_block = src.split("function applyLabCanvasServerReplayFrame(", 1)[1]
    assert 'classList.add("lab-replay-grid--canvas-mode")' in apply_block[:2500]


def test_lab_replay_hooks_preserved() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "window.AsteroidLabReplay" in src
    assert "renderReplayFrame:" in src
    assert "applyLabCanvasServerReplayFrame" in src


def test_lab_map_z_layer_picker_contract() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    tpl = TPL.read_text(encoding="utf-8")
    assert "LAB_MAP_Z_LAYER_OPTIONS" in src
    assert "All layers" in src
    assert "L=0 · Floor" in src
    assert "L=1 · Layer 1" in src
    assert "L=2 · Layer 2" in src
    assert "function labCellMapZ(" in src
    assert "LabReplayHeightLayer.resolveReplayHeightLayerForWireRow" in src
    assert "function inferLabCellMapZ(" not in src
    assert "function cellPassesMapZFilter(" in src
    assert 'id="lab-replay-layer-picker"' in tpl
    assert 'id="lab-replay-grid-viewport"' in tpl
    assert "Height layer (L)" in tpl
    assert "flex-col-reverse" in tpl
    assert 'lab-replay-layer-picker"' in tpl
    assert "absolute bottom-2 right-2" in tpl
    assert 'input.type = "radio"' in src
    assert "labMapZSelectedLayer" in src


def test_lab_js_collect_overlay_paint_targets_uses_registry() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function collectOverlayPaintTargets(", 1)[1].split(
        "function isSparseReplayFrame(", 1
    )[0]
    assert "LabReplayOverlayBucketRegistry.collectOverlayCellsForPaintTarget" in body
    assert "equipment_bundles" in body


def test_collect_replay_spatial_coords_includes_cell_overlay_json() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    idx = src.find("function collectReplaySpatialCoordsForLayout(frame)")
    assert idx >= 0
    body = src[idx : idx + 950]
    assert "fullMapCellsFromFrame(frame)" in body
    assert "labCellsFromMapView(mapView)" in body
    assert "cellOverlayJsonFromFrame(frame)" in body
    assert "collectOverlayPaintTargets(overlayJson)" in body


def test_js_sanitize_replay_wire_cell_for_read_exists() -> None:
    src = SANITIZE_JS.read_text(encoding="utf-8")
    assert "function sanitizeReplayWireCellForRead" in src
    assert "function cellKey" in src
    assert "LabReplayWireSanitize" in src


def test_js_sanitizer_matches_python_candidate_compat_cases() -> None:
    src = SANITIZE_JS.read_text(encoding="utf-8")
    assert '"shape_belt"' in src  # legacy compat token handled in sanitizer
    assert "output_transport_kind" in src
    assert "candidate_miner" in src
    assert "space_belt" in src
    assert "function isCandidateOutputHintKind" in src


def test_lab_sprite_path_handles_space_belt_transport_wire() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "function normalizeReplayWireCell(" in src
    assert "function inferTransportSpriteIdentifier(" in src
    assert 'tk === "space_belt"' in src
    assert (
        "overlayCellKind(cell)" in src.split("function inferTransportSpriteIdentifier(", 1)[1][:700]
    )
    assert "SpaceBelt_Forward" in src


def test_js_lab_replay_overlay_bucket_registry_module_contract() -> None:
    src = OVERLAY_REGISTRY_JS.read_text(encoding="utf-8")
    assert "LabReplayOverlayBucketRegistry" in src
    assert "collectOverlayCellsForPaintTarget" in src


def test_js_lab_replay_height_layer_module_contract() -> None:
    src = HEIGHT_JS.read_text(encoding="utf-8")
    assert "LabReplayHeightLayer" in src
    assert "enrichReplayWireRowWithLayer" in src


def test_js_paint_plan_enriches_height_layer_before_index() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "enrichWireRowWithLayer" in src
    index_body = src.split("function buildEffectiveCellViewIndex(", 1)[1].split(
        "function buildEffectiveCellViewIndexWithCarry(", 1
    )[0]
    assert "enrichWireRowWithLayer" in index_body


def test_js_lab_paint_layers_from_view_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function labPaintLayersFromView" in src
    assert "function buildEffectiveCellViewIndex" in src
    assert "LabReplayPaintPlan" in src


def test_template_loads_lab_replay_paint_plan_js() -> None:
    tpl = TPL.read_text(encoding="utf-8")
    assert "lab_replay_height_layer.js" in tpl
    assert "lab_replay_overlay_bucket_registry.js" in tpl
    assert "lab_replay_paint_plan.js" in tpl
    assert tpl.index("lab_effective_cell_view.js") < tpl.index("lab_replay_height_layer.js")
    height_idx = tpl.index("lab_replay_height_layer.js")
    registry_idx = tpl.index("lab_replay_overlay_bucket_registry.js")
    paint_idx = tpl.index("lab_replay_paint_plan.js")
    assert height_idx < registry_idx
    assert registry_idx < paint_idx


def test_js_paint_plan_contains_candidate_priority_guard() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "candidate_miner" in src
    assert "candidate_ring" in src
    transport_fn = src.split("function resolveTransport(", 1)[1]
    candidate_idx = transport_fn.index("candidate_miner")
    guard_region = transport_fn[candidate_idx : candidate_idx + 120]
    assert "null" in guard_region


def test_js_paint_plan_map_z_filter_helpers() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function effectiveWirePassesMapZFilter(" in src
    assert "selectedMapZLayer" in src
    body = src.split("function buildLabPaintPlanFromFrame(", 1)[1].split(
        "function collectSpriteRelsFromPaintPlanFrames(", 1
    )[0]
    assert "effectiveWirePassesMapZFilter(wire, ck, options)" in body


def test_js_build_lab_paint_plan_from_frame_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function buildLabPaintPlanFromFrame" in src
    assert "buildLabPaintPlanFromFrame:" in src
    assert "lastFrameWithSpriteCapableCells" in src
    assert "mergeCarriedIndexKeys" in src
    assert "Layout carry" in src


def test_js_canvas_plan_from_paint_layers_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function canvasPlanFromPaintLayers" in src
    assert "canvasPlanFromPaintLayers:" in src
    assert "CANDIDATE_RING_STROKE" in src
    assert 'kind: "candidate_ring"' in src
    assert "isRgbaFill" in src


def test_js_dom_plan_from_paint_layers_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function domPlanFromPaintLayers" in src
    assert "domPlanFromPaintLayers:" in src
    assert "lab-overlay-candidate-miner-ring" in src
    assert "skipFullFill" in src


def test_js_slice_c_dom_plan_builder_and_render_authority() -> None:
    paint_src = PAINT_JS.read_text(encoding="utf-8")
    assert "function buildDomPlanForCell" in paint_src
    assert "function resolveDomPlanForWire" in paint_src
    assert "wireDataAttrsFromEffectiveWire" in paint_src
    resolver_body = paint_src.split("function buildDomPlanResolverForFrame(", 1)[1].split(
        "function coordFromWireOrKey(", 1
    )[0]
    assert "buildDomPlanForCell(wire)" in resolver_body
    assert "sources.overlay_cells" not in resolver_body

    lab_src = LAB_JS.read_text(encoding="utf-8")
    assert "function applyDomPlanToCell(" in lab_src
    render_body = lab_src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "applyDomPlanToCell(" in render_body
    assert "toneForFullMapCell(cell, frame)" not in render_body
    assert "sources.overlay_cells" not in render_body
    token_body = lab_src.split("function labPaintTokenForCell(", 1)[1].split(
        "function frameCellIndexMap(", 1
    )[0]
    assert "cellRenderToken" in token_body
    assert "domPlan.hudRole" in token_body or "domPlan.dataAttrs" in token_body


def test_js_b2_semantic_display_model_projection() -> None:
    src = EFFECTIVE_CELL_JS.read_text(encoding="utf-8")
    assert "function effectiveCellViewDisplayModel" in src
    model_body = src.split("function effectiveCellViewDisplayModel(", 1)[1].split(
        "function effectiveCellViewDisplaySections(", 1
    )[0]
    sections_body = src.split("function effectiveCellViewDisplaySections(", 1)[1].split(
        "function effectiveCellViewDisplayRows(", 1
    )[0]
    assert "effectiveCellViewDisplayModel" in sections_body
    assert 'id: "machine"' in model_body
    assert "Facing:" in model_body
    assert "Output:" in model_body
    assert 'title: "Sprite"' not in model_body
    assert "Output requirement" not in model_body


def test_js_overlay_output_hint_for_candidate_miner() -> None:
    src = EFFECTIVE_CELL_JS.read_text(encoding="utf-8")
    hint_body = src.split("function isOverlayOutputHint(", 1)[1].split(
        "function hasMachineSummary(", 1
    )[0]
    assert "isOverlaySemanticKind" in hint_body
    diag_body = src.split("function effectiveCellViewDisplayDiagnostics(", 1)[1].split(
        "global.LabEffectiveCellView", 1
    )[0]
    assert "Merge inputs" not in diag_body
    assert "Map view hits" not in diag_body
    assert "Wire kind" not in diag_body


def test_js_b2_overlay_semantic_kinds_skip_machine_summary() -> None:
    src = EFFECTIVE_CELL_JS.read_text(encoding="utf-8")
    assert "function isOverlaySemanticKind" in src
    assert "function effectiveCellViewDisplayDiagnostics" in src
    machine_body = src.split("function hasMachineSummary(", 1)[1].split(
        "function effectiveCellViewDisplayModel(", 1
    )[0]
    assert "isOverlaySemanticKind" in machine_body


def test_js_effective_cell_canonical_detail_sections() -> None:
    src = EFFECTIVE_CELL_JS.read_text(encoding="utf-8")
    assert "function effectiveCellViewDisplaySections" in src
    assert "Requires output:" in src
    display_body = src.split("function effectiveCellViewDisplayModel(", 1)[1].split(
        "function effectiveCellViewDisplaySections(", 1
    )[0]
    assert "sources.overlay_cells" not in display_body
    assert "sources.full_cell" not in display_body
    assert "transport_tile" not in display_body
    assert "sprite_identifier" not in display_body
    assert "tile_type" not in display_body


def test_js_lab_detail_panel_uses_canonical_sections() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "effectiveCellViewDisplaySections" in src
    assert "labEffectiveCellDetailSectionsHtml" in src
    render_body = src.split("function labCellDetailRenderSuccess(", 1)[1].split(
        "const cellDetailModal =", 1
    )[0]
    assert "labEffectiveCellDiagnosticsHtml" in render_body
    assert "Diagnostics" in render_body
    assert "Source wires" not in render_body
    assert "Raw sources / debug evidence" not in render_body
    assert "sources.overlay_cells" not in render_body.split("labEffectiveCellDetailSectionsHtml")[0]
    detail_html_body = src.split("function labEffectiveCellDetailSectionsHtml(", 1)[1].split(
        "function labCellDetailRenderSuccess(", 1
    )[0]
    assert "sources." not in detail_html_body


def test_js_effective_cell_merge_carries_overlay_role() -> None:
    src = EFFECTIVE_CELL_JS.read_text(encoding="utf-8")
    assert "overlay_role:" in src
    assert "OVERLAY_SEMANTIC_KINDS" in src
    assert "overlayRoleFromCell" in src


def test_js_paint_plan_uses_merged_overlay_role_not_raw_sources() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "overlayRoleFromWireSources" not in src
    resolver_body = src.split("function buildDomPlanResolverForFrame(", 1)[1].split(
        "function coordFromWireOrKey(", 1
    )[0]
    assert "buildDomPlanForCell(wire)" in resolver_body
    attrs_body = src.split("function wireDataAttrsFromEffectiveWire(", 1)[1].split(
        "function resolveHudRoleFromWire(", 1
    )[0]
    assert "wire.overlay_role" in attrs_body
    cell_like_body = src.split("function cellLikeFromEffectiveWire(", 1)[1].split(
        "function buildCellByGridIndexFromFrame(", 1
    )[0]
    assert "wire.overlay_role" in cell_like_body
    assert "sources.overlay_cells" not in cell_like_body


def test_js_build_dom_plan_resolver_for_frame_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function buildDomPlanResolverForFrame" in src
    assert "buildDomPlanResolverForFrame:" in src
    resolver_body = src.split("function buildDomPlanResolverForFrame", 1)[1][:900]
    assert "buildEffectiveCellViewIndexWithCarry" in resolver_body
    assert "return function" in resolver_body


def test_js_build_cell_by_grid_index_from_frame_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function buildCellByGridIndexFromFrame" in src
    assert "buildCellByGridIndexFromFrame:" in src


def test_lab_js_lab_paint_v2_enabled_helper() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "function labPaintLegacyOptIn(" in src
    assert "function labPaintV2Enabled(" in src
    legacy_body = src.split("function labPaintLegacyOptIn(", 1)[1][:320]
    assert "lab-root" in legacy_body
    assert 'ds.labPaintLegacy === "1"' in legacy_body
    assert 'ds.labPaintV2 === "0"' in legacy_body
    enabled_body = src.split("function labPaintV2Enabled(", 1)[1][:120]
    assert "labPaintLegacyOptIn()" in enabled_body

    plan_body = src.split("function buildCanvasPaintPlan(", 1)[1].split(
        "function refreshLabCanvasAfterLayoutChange(", 1
    )[0]
    assert "labPaintV2Enabled()" not in plan_body
    assert "LabReplayPaintPlan.buildLabPaintPlanFromFrame" in plan_body
    assert "resolveCellIndex" in plan_body
    assert "replayArrayIndex" in plan_body
    assert "replayFrames" in plan_body
    assert "hasServerReplay" in plan_body
    assert "selectedMapZLayer" in plan_body
    assert "labMapZSelectedLayer" in plan_body


def test_lab_js_paint_d_prime_flag_contract_step_6_1() -> None:
    """Step 6.1: D′ default v2; legacy opt-in retained for flag helper only post-6.4."""
    src = LAB_JS.read_text(encoding="utf-8")
    legacy_body = src.split("function labPaintLegacyOptIn(", 1)[1].split(
        "function labPaintV2Enabled(", 1
    )[0]
    assert 'ds.labPaintLegacy === "1"' in legacy_body
    assert 'ds.labPaintV2 === "0"' in legacy_body
    enabled_body = src.split("function labPaintV2Enabled(", 1)[1][:160]
    assert "!labPaintLegacyOptIn()" in enabled_body.replace(" ", "")
    assert "function resolveSpriteRelForStandaloneOverlayCell(" in src
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "createDomPlanResolverForFrame" in render_body
    assert "candidateObservationToneClasses" not in render_body
    canvas_fn = src.split("function buildCanvasPaintPlan(", 1)[1].split(
        "function refreshLabCanvasAfterLayoutChange(", 1
    )[0]
    assert "stageCell" not in canvas_fn
    assert "const overlays = []" not in canvas_fn


def test_lab_js_filter_terrain_cells_for_paint_v2_exists() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "function filterTerrainCellsForPaintV2(" in src
    filter_body = src.split("function filterTerrainCellsForPaintV2(", 1)[1].split(
        "function syncLabTerrainCanvasLayer(", 1
    )[0]
    assert "labPaintV2Enabled()" not in filter_body
    assert "LabReplayPaintPlan.buildLabPaintPlanFromFrame" in filter_body
    assert "AsteroidField_Fluid.svg" in filter_body
    assert "AsteroidField_Shape.svg" in filter_body

    refresh_block = src.split("function refreshLabCanvasAfterLayoutChange(", 1)[1][:1200]
    assert "filterTerrainCellsForPaintV2(" in refresh_block

    canvas_frame_block = src.split("function applyLabCanvasServerReplayFrame(", 1)[1][:1400]
    assert "filterTerrainCellsForPaintV2(" in canvas_frame_block


def test_lab_js_dom_paint_v2_wiring_in_token_and_render() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "function createDomPlanResolverForFrame(" in src
    assert "function labDomPaintOptionsFromContext(" in src
    assert "LabReplayPaintPlan.buildDomPlanResolverForFrame" in src
    token_body = src.split("function labPaintTokenForCell(", 1)[1].split(
        "function frameCellIndexMap(", 1
    )[0]
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "resolveDomPlan" in token_body or "domPlan" in token_body
    assert "createDomPlanResolverForFrame" in render_body
    assert render_body.index("createDomPlanResolverForFrame") < render_body.index("for (let i = 0")
    assert "domPlan" in render_body or "skipFullFill" in render_body


def test_lab_js_detail_lookup_untouched() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    detail_body = src.split("function labCellDetailLookupInMapView(", 1)[1].split(
        "function labCellDetailFromTimelineFrame(", 1
    )[0]
    assert "LabReplayPaintPlan" not in detail_body
    assert "buildDomPlanResolverForFrame" not in detail_body
    assert "mergeEffectiveCellView" in detail_body


def test_lab_js_replay_dom_resolver_flag_independent_step_6_4() -> None:
    """Step 6.4: replay DOM resolver always built; legacy opt-in no longer gates resolver."""
    src = LAB_JS.read_text(encoding="utf-8")
    resolver_body = src.split("function createDomPlanResolverForFrame(", 1)[1][:450]
    assert "labPaintV2Enabled()" not in resolver_body
    assert "LabReplayPaintPlan.buildDomPlanResolverForFrame" in resolver_body
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "createDomPlanResolverForFrame" in render_body
    assert render_body.index("createDomPlanResolverForFrame") < render_body.index("for (let i = 0")


def test_warmup_sprite_collect_uses_paint_plan() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function collectSpriteRelpathsFromFrames(", 1)[1][:500]
    assert "collectSpriteRelsFromPaintPlanFrames" in body
    assert "labPaintV2Enabled()" not in body
    assert "collectFrameSpatialTargets" not in body
    assert "collectReplaySpatialCoordsForLayout" not in body


def test_lab_js_non_sprite_policy_step_6_6() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    resolver_body = src.split("function resolveSpriteRelForStandaloneOverlayCell(", 1)[1].split(
        "function attachLabSpriteImgNoDrag(", 1
    )[0]
    assert "isCandidateMinerOverlayKind(ck)" in resolver_body
    assert "lab-overlay-candidate-miner" in src
    non_sprite = src.split("var NON_SPRITE_OVERLAY_CELL_KINDS = {", 1)[1].split("};", 1)[0]
    assert "candidate_miner" not in non_sprite
    assert "candidate_transport_stub: true" in non_sprite
    assert "candidate_route_path: true" in non_sprite
    assert "route_path: true" in non_sprite
    obs_body = src.split("function isCandidateObservationOverlayKind(", 1)[1].split(
        "function toneForRouteOverlayKind(", 1
    )[0]
    assert "isCandidateMinerOverlayKind(ck)" in obs_body
