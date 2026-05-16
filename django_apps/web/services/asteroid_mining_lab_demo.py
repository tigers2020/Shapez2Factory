"""Static demo payload for the asteroid mining lab page (no solver wiring)."""

from __future__ import annotations

from typing import Any

TOTAL_FRAMES = 240

LAB_CELL_BASE = "lab-cell h-5 w-5 shrink-0 rounded-[5px] border"


def _logical_cell(x: int, y: int) -> dict[str, Any]:
    cx, cy = 11, 7
    dx, dy = abs(x - cx), abs(y - cy)
    dist = dx * 1.15 + dy * 1.05
    in_asteroid = dist < 9.2 and not (dx < 3 and dy < 2)
    rim = in_asteroid and dist > 7.2
    void_cell = not in_asteroid
    internal_void = dx < 3 and dy < 2
    candidate = in_asteroid and ((x + y * 2) % 7 == 0 or (x * 3 + y) % 11 == 0)
    confirmed = in_asteroid and ((x + y) % 13 == 0 or (x * 2 + y) % 17 == 0)
    route = in_asteroid and (y == 7 or x == 17) and x > 11
    return {
        "x": x,
        "y": y,
        "rim": rim,
        "void_cell": void_cell,
        "internal_void": internal_void,
        "candidate": candidate,
        "confirmed": confirmed,
        "route": route,
    }


def _cell_classes_for_overlay(c: dict[str, Any], overlay: str) -> str:
    if overlay == "candidates" and c["candidate"]:
        return f"{LAB_CELL_BASE} bg-cyan-500/80 border-cyan-300"
    if overlay == "routes" and c["route"]:
        return f"{LAB_CELL_BASE} bg-emerald-500/90 border-emerald-300"
    if overlay == "confirmed" and c["confirmed"]:
        return f"{LAB_CELL_BASE} bg-violet-500/90 border-violet-300"

    if c["internal_void"]:
        return f"{LAB_CELL_BASE} bg-slate-900 border-slate-800"
    if not c["void_cell"] and not c["internal_void"]:
        if c["rim"]:
            return f"{LAB_CELL_BASE} bg-amber-900/70 border-amber-700/70"
        return f"{LAB_CELL_BASE} bg-stone-800 border-stone-700"
    return f"{LAB_CELL_BASE} bg-slate-950 border-slate-900"


def build_lab_cells_overlay_matrix() -> list[list[str]]:
    out: list[list[str]] = []
    for i in range(23 * 15):
        x, y = i % 23, i // 23
        c = _logical_cell(x, y)
        out.append(
            [
                _cell_classes_for_overlay(c, "candidates"),
                _cell_classes_for_overlay(c, "routes"),
                _cell_classes_for_overlay(c, "confirmed"),
            ]
        )
    return out


RUNS: list[dict[str, Any]] = [
    {
        "id": "G-042",
        "score": 91.4,
        "miners": 42,
        "connected": 40,
        "cost": 118,
        "belts": 8,
        "pipes": 2,
        "saturation": 96,
        "status": "best",
    },
    {
        "id": "G-039",
        "score": 88.7,
        "miners": 43,
        "connected": 37,
        "cost": 141,
        "belts": 9,
        "pipes": 2,
        "saturation": 89,
        "status": "risky",
    },
    {
        "id": "G-036",
        "score": 86.2,
        "miners": 39,
        "connected": 39,
        "cost": 109,
        "belts": 8,
        "pipes": 1,
        "saturation": 92,
        "status": "stable",
    },
    {
        "id": "G-031",
        "score": 79.8,
        "miners": 45,
        "connected": 30,
        "cost": 177,
        "belts": 9,
        "pipes": 3,
        "saturation": 67,
        "status": "rejected",
    },
]

EXTRACTOR_RULES: list[dict[str, str]] = [
    {
        "label": "Single asteroid cell",
        "value": "6.4 items/s",
        "detail": "0.4 × 16 shape extraction",
    },
    {
        "label": "Single fluid cell",
        "value": "28,800 L/min",
        "detail": "1,800 × 16 fluid extraction",
    },
    {"label": "Extractor multiplier", "value": "x4 base", "detail": "base extractor output scale"},
    {"label": "Extension multiplier", "value": "+x12 max", "detail": "3 extensions × x4 each"},
    {
        "label": "Bundle total",
        "value": "x16 total",
        "detail": "x4 extractor + x12 extension network",
    },
]

TOPOLOGY_RULES: list[dict[str, str]] = [
    {"label": "Extension cap", "value": "max 3", "detail": "per extractor bundle"},
    {
        "label": "Attachment",
        "value": "Extractor / Extension",
        "detail": "extension can chain from either",
    },
    {
        "label": "Connection side",
        "value": "R-facing",
        "detail": "module R direction defines attachment validity",
    },
    {
        "label": "Output rule",
        "value": "required transport",
        "detail": "belt/pipe must attach to extractor output",
    },
    {
        "label": "Transport merge",
        "value": "auto-connect",
        "detail": "adjacent same-kind belt/pipe cells connect automatically",
    },
]

STAGES: list[dict[str, str]] = [
    {"label": "Decode", "state": "done", "icon": "cpu"},
    {"label": "Reconstruct", "state": "done", "icon": "grid"},
    {"label": "Patterns", "state": "active", "icon": "sparkles"},
    {"label": "Evolution", "state": "active", "icon": "git-branch"},
    {"label": "Route Probe", "state": "active", "icon": "route"},
    {"label": "Validate", "state": "pending", "icon": "check"},
]


def assert_ui_model() -> None:
    matrix = build_lab_cells_overlay_matrix()
    if len(matrix) != 23 * 15:
        raise RuntimeError("Expected 23x15 replay grid.")
    if len(TOPOLOGY_RULES) < 5:
        raise RuntimeError("Topology modal must expose all core bundle rules.")
    if not any(r["value"] == "x16 total" for r in EXTRACTOR_RULES):
        raise RuntimeError("Extractor constraint panel must include x16 total bundle output.")
    if any(int(r["connected"]) > int(r["miners"]) for r in RUNS):
        raise RuntimeError("Connected miners cannot exceed total miners.")


assert_ui_model()


_OVERLAY_KEYS = ("candidates", "routes", "confirmed")


def replay_overlay_for_frame(frame: int) -> str:
    if frame < 90:
        return "candidates"
    if frame < 150:
        return "routes"
    return "confirmed"


def replay_phase_for_frame(frame: int) -> str:
    if frame < 40:
        return "Decode + Reconstruction"
    if frame < 90:
        return "Candidate Expansion"
    if frame < 150:
        return "Route Feasibility"
    return "Final Validation"


def initial_cell_classes(matrix: list[list[str]], frame: int) -> list[str]:
    oi = _OVERLAY_KEYS.index(replay_overlay_for_frame(frame))
    return [row[oi] for row in matrix]


def _stage_tone_class(state: str) -> str:
    if state == "done":
        return "bg-emerald-500/15 text-emerald-300"
    if state == "active":
        return "bg-cyan-500/15 text-cyan-300"
    return "bg-slate-800 text-slate-500"


def lab_page_context() -> dict[str, Any]:
    matrix = build_lab_cells_overlay_matrix()
    initial_frame = 128
    stages_display = [{**s, "tone_class": _stage_tone_class(s["state"])} for s in STAGES]
    default_run = RUNS[0] if RUNS else None
    return {
        "total_frames": TOTAL_FRAMES,
        "initial_frame": initial_frame,
        "initial_replay_phase": replay_phase_for_frame(initial_frame),
        "lab_cell_initial_classes": initial_cell_classes(matrix, initial_frame),
        "lab_cell_overlay_matrix": matrix,
        "runs": RUNS,
        "extractor_rules": EXTRACTOR_RULES,
        "topology_rules": TOPOLOGY_RULES,
        "stages_display": stages_display,
        "lab_ui_initial": {
            "frame": initial_frame,
            "totalFrames": TOTAL_FRAMES,
            "blueprintCode": "",
            "defaultRun": default_run,
            "defaultRunId": default_run["id"] if default_run else None,
        },
    }
