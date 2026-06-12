"""PR-RENDER-5: canvas overlay + sprite renderer contracts."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS_DIR = REPO / "django_apps" / "web" / "static" / "web" / "js"
TPL = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
LAB_JS = JS_DIR / "asteroid_miner_layout_lab.js"
SANITIZE_JS = JS_DIR / "lab_replay_wire_sanitize.js"
PAINT_JS = JS_DIR / "lab_replay_paint_plan.js"


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
    assert "function lastFrameWithSpriteCapableCells(" in src
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
    assert "function inferLabCellMapZ(" in src
    assert "function cellPassesMapZFilter(" in src
    assert 'id="lab-replay-layer-picker"' in tpl
    assert 'id="lab-replay-grid-viewport"' in tpl
    assert "Height layer (L)" in tpl
    assert "flex-col-reverse" in tpl
    assert 'lab-replay-layer-picker"' in tpl
    assert "absolute bottom-3 right-3" in tpl
    assert 'input.type = "radio"' in src
    assert "labMapZSelectedLayer" in src


def test_collect_frame_spatial_targets_includes_cell_overlay_json() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    idx = src.find("function collectFrameSpatialTargets(frame)")
    body = src[idx : idx + 900]
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


def test_js_lab_paint_layers_from_view_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function labPaintLayersFromView" in src
    assert "function buildEffectiveCellViewIndex" in src
    assert "LabReplayPaintPlan" in src


def test_template_loads_lab_replay_paint_plan_js() -> None:
    tpl = TPL.read_text(encoding="utf-8")
    assert "lab_replay_paint_plan.js" in tpl
    assert tpl.index("lab_effective_cell_view.js") < tpl.index("lab_replay_paint_plan.js")


def test_js_paint_plan_contains_candidate_priority_guard() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "candidate_miner" in src
    assert "candidate_ring" in src
    transport_fn = src.split("function resolveTransport(", 1)[1]
    candidate_idx = transport_fn.index("candidate_miner")
    guard_region = transport_fn[candidate_idx : candidate_idx + 120]
    assert "null" in guard_region
