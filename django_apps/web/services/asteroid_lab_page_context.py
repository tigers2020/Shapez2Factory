"""Default template context for the asteroid mining lab page (no demo payload)."""

from __future__ import annotations

from typing import Any

GRID_W, GRID_H = 23, 15
CELL_COUNT = GRID_W * GRID_H

LAB_CELL_NEUTRAL = "lab-cell h-5 w-5 shrink-0 rounded-[5px] border bg-slate-950 border-slate-900"


def _neutral_overlay_matrix() -> list[list[str]]:
    row = [LAB_CELL_NEUTRAL, LAB_CELL_NEUTRAL, LAB_CELL_NEUTRAL]
    return [list(row) for _ in range(CELL_COUNT)]


def lab_page_context() -> dict[str, Any]:
    matrix = _neutral_overlay_matrix()
    initial_frame = 0
    total_frames = 0
    initial_classes = [row[0] for row in matrix]
    return {
        "total_frames": total_frames,
        "initial_frame": initial_frame,
        "initial_replay_phase": "—",
        "lab_cell_initial_classes": initial_classes,
        "lab_cell_overlay_matrix": matrix,
        "runs": [],
        "extractor_rules": [],
        "topology_rules": [],
        "stages_display": [],
        "lab_ui_initial": {
            "frame": initial_frame,
            "totalFrames": total_frames,
            "blueprintCode": "",
        },
    }
