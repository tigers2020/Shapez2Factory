"""PR-RENDER-4: canvas static terrain layer contracts."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS_DIR = REPO / "django_apps" / "web" / "static" / "web" / "js"
TPL = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
LAB_JS = JS_DIR / "asteroid_miner_layout_lab.js"


def test_terrain_module_exports_draw() -> None:
    src = (JS_DIR / "lab_replay_canvas_terrain.js").read_text(encoding="utf-8")
    assert "drawTerrainLayer" in src
    assert "isStaticTerrainCell" in src


def test_template_has_terrain_canvas() -> None:
    tpl = TPL.read_text(encoding="utf-8")
    assert 'id="lab-replay-terrain-canvas"' in tpl
    assert "lab_replay_canvas_terrain.js" in tpl


def test_lab_js_wires_terrain_canvas_sync() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    assert "function syncLabTerrainCanvasLayer(" in src
    assert "labTerrainCanvasEnabled" in src
    assert "isLabStaticTerrainCell" in src
