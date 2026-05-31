"""PR-RENDER-5: canvas overlay + sprite renderer contracts."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS_DIR = REPO / "django_apps" / "web" / "static" / "web" / "js"
TPL = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
LAB_JS = JS_DIR / "asteroid_miner_layout_lab.js"


def test_canvas_renderer_module_contract() -> None:
    src = (JS_DIR / "lab_replay_canvas_renderer.js").read_text(encoding="utf-8")
    assert "createLabCanvasRenderer" in src
    assert "drawFrame" in src
    assert "hitTest" in src
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
