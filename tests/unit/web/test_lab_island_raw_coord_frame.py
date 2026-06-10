"""Lab island-local coord frame contract (replay UI must not apply world-map x skip)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
LAB_JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
TERRAIN_JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "lab_replay_canvas_terrain.js"
TEMPLATE = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"

LAB_COORD_BUILD = "island_raw_v2"
LAB_JS_CACHE_BUILD = "island_raw_v4"
REPLAY_GRID_EDGE_PADDING = 5


def _visual_col_identity(x: int) -> int:
    return x


def _visual_col_world_map(x: int) -> int:
    if x < 0:
        return x
    if x > 0:
        return x - 1
    return 0


def _compute_replay_layout(cells: list[dict[str, int]], visual_col) -> dict[str, int]:
    min_d = min(visual_col(c["x"]) for c in cells)
    max_d = max(visual_col(c["x"]) for c in cells)
    min_r = min(c["y"] for c in cells)
    max_r = max(c["y"] for c in cells)
    core_half_x = max(max(0, -min_d), max(0, max_d), 1)
    core_half_y = max(max(0, -min_r), max(0, max_r), 1)
    half_x = core_half_x + REPLAY_GRID_EDGE_PADDING
    half_y = core_half_y + REPLAY_GRID_EDGE_PADDING
    return {
        "minD": -half_x,
        "minR": -half_y,
        "gridW": 2 * half_x + 1,
        "gridH": 2 * half_y + 1,
    }


def _cell_index(cell: dict[str, int], layout: dict[str, int], visual_col) -> int | None:
    d = visual_col(cell["x"])
    col = d - layout["minD"]
    row = cell["y"] - layout["minR"]
    if col < 0 or row < 0 or col >= layout["gridW"] or row >= layout["gridH"]:
        return None
    return row * layout["gridW"] + col


def _layout_collision_count(cells: list[dict[str, int]], visual_col) -> int:
    layout = _compute_replay_layout(cells, visual_col)
    seen: dict[int, tuple[int, int]] = {}
    collisions = 0
    for cell in cells:
        idx = _cell_index(cell, layout, visual_col)
        if idx is None:
            continue
        key = (cell["x"], cell["y"])
        if idx in seen and seen[idx] != key:
            collisions += 1
        seen[idx] = key
    return collisions


def test_lab_js_run_solver_in_flight_declared_before_first_sync() -> None:
    js = LAB_JS.read_text(encoding="utf-8")
    init_idx = js.index("function init(")
    init_body = js[init_idx:]
    first_sync = init_body.index("syncLabActionButtons();")
    in_flight_decl = init_body.index("let runSolverInFlight")
    assert in_flight_decl < first_sync


def test_lab_js_declares_island_raw_coord_build_and_identity_visual_col() -> None:
    js = LAB_JS.read_text(encoding="utf-8")
    assert f'LAB_COORD_FRAME_BUILD = "{LAB_JS_CACHE_BUILD}"' in js
    assert "return xi;" in js[js.index("function visualCol") : js.index("function cellIndexDemo")]
    assert "x - 1" not in js[js.index("function visualCol") : js.index("function cellIndexDemo")]
    assert "const xWorld = d;" in js
    dom_slice = js[
        js.index("function domIndexToWorldXY") : js.index("function findLabCellFromPoint")
    ]
    assert "d + 1" not in dom_slice


def test_lab_template_cache_busts_coord_frame_scripts() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    assert "asteroid_miner_layout_lab.js' %}?v=" + LAB_JS_CACHE_BUILD in template
    assert "lab_replay_canvas_terrain.js' %}?v=" + LAB_COORD_BUILD in template


def test_terrain_js_matches_island_raw_coord_build() -> None:
    js = TERRAIN_JS.read_text(encoding="utf-8")
    assert f'LAB_COORD_FRAME_BUILD = "{LAB_COORD_BUILD}"' in js


def test_identity_visual_col_avoids_x0_x1_grid_collision() -> None:
    cells = [
        {"x": 0, "y": 3},
        {"x": 1, "y": 3},
        {"x": -1, "y": 3},
        {"x": 2, "y": 4},
    ]
    assert _layout_collision_count(cells, _visual_col_world_map) >= 1
    assert _layout_collision_count(cells, _visual_col_identity) == 0


@pytest.mark.django_db
def test_fluid_run_replay_cells_have_zero_layout_collisions_under_identity_visual_col() -> None:
    pytest.importorskip("django")
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
        compose_lab_replay_frames_from_artifact_run,
    )

    run = m.SolverRun.objects.filter(id=426).first()
    if run is None:
        pytest.skip("run #426 not in database")
    frames = compose_lab_replay_frames_from_artifact_run(run)
    assert frames
    last = frames[-1]
    map_view = last.get("map_view") or {}
    cells: list[dict[str, int]] = []
    for row in map_view.get("full_cells") or []:
        if isinstance(row, dict) and row.get("x") is not None and row.get("y") is not None:
            cells.append({"x": int(row["x"]), "y": int(row["y"])})
    for row in map_view.get("overlay_cells") or []:
        if isinstance(row, dict) and row.get("x") is not None and row.get("y") is not None:
            cells.append({"x": int(row["x"]), "y": int(row["y"])})
    assert cells
    assert _layout_collision_count(cells, _visual_col_identity) == 0
