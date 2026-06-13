"""Parity: lab_replay_overlay_bucket_registry.js mirrors Python registry."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from django_apps.asteroid_lab.replay.replay_overlay_bucket_registry import (
    OverlayBucketRole,
    collect_overlay_cells_for_paint_target,
    collect_overlay_cells_for_semantic_lookup,
    overlay_bucket_keys_for_role,
)

REPO = Path(__file__).resolve().parents[4]
REGISTRY_JS = (
    REPO / "django_apps" / "web" / "static" / "web" / "js" / "lab_replay_overlay_bucket_registry.js"
)
PAINT_JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "lab_replay_paint_plan.js"
PARITY_SCRIPT = REPO / "scripts" / "run_lab_replay_overlay_bucket_registry_parity.mjs"

PARITY_CASES: list[dict[str, object]] = [
    {
        "keys_role": "paint_target",
        "expected_keys": list(overlay_bucket_keys_for_role(OverlayBucketRole.PAINT_TARGET)),
    },
    {
        "keys_role": "semantic_lookup",
        "expected_keys": list(overlay_bucket_keys_for_role(OverlayBucketRole.SEMANTIC_LOOKUP)),
    },
    {
        "role": "paint_target",
        "overlay": {
            "equipment_bundles": [
                {"cells_json": [{"x": 3, "y": 0, "cell_kind": "fluid_miner"}]},
            ],
            "components": [{"cells": [{"x": 4, "y": 0, "cell_kind": "candidate_miner"}]}],
        },
        "expected_kinds": ["fluid_miner"],
    },
    {
        "role": "semantic_lookup",
        "overlay": {
            "cells": [{"x": 1, "y": 0, "cell_kind": "space_belt"}],
            "custom_bundle": {"cells_json": [{"x": 2, "y": 0, "cell_kind": "space_pipe"}]},
        },
        "expected_kinds": ["space_belt", "space_pipe"],
    },
]


def _kind_set(rows: list[dict[str, object]]) -> set[str]:
    return {str(c.get("cell_kind") or c.get("kind") or "") for c in rows}


def test_python_paint_target_keys_include_equipment_bundles() -> None:
    keys = overlay_bucket_keys_for_role(OverlayBucketRole.PAINT_TARGET)
    assert "equipment_bundles" in keys
    assert "components" not in keys


@pytest.mark.parametrize(
    "case",
    [c for c in PARITY_CASES if c.get("role") == "paint_target"],
    ids=["paint_harvest"],
)
def test_python_paint_harvest_cases(case: dict[str, object]) -> None:
    overlay = dict(case["overlay"])  # type: ignore[arg-type]
    expected = set(case["expected_kinds"])  # type: ignore[arg-type]
    got = _kind_set(collect_overlay_cells_for_paint_target(overlay))
    assert got == expected


@pytest.mark.parametrize(
    "case",
    [c for c in PARITY_CASES if c.get("role") == "semantic_lookup"],
    ids=["semantic_harvest"],
)
def test_python_semantic_harvest_cases(case: dict[str, object]) -> None:
    overlay = dict(case["overlay"])  # type: ignore[arg-type]
    expected = set(case["expected_kinds"])  # type: ignore[arg-type]
    got = _kind_set(collect_overlay_cells_for_semantic_lookup(overlay))
    assert got == expected


def test_js_overlay_registry_module_contract() -> None:
    src = REGISTRY_JS.read_text(encoding="utf-8")
    assert "LabReplayOverlayBucketRegistry" in src
    assert "collectOverlayCellsForPaintTarget" in src
    assert "equipment_bundles" in src
    assert "replay_overlay_bucket_registry.py" in src


def test_js_paint_plan_delegates_overlay_json_harvest_to_registry() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    body = src.split("function overlayJsonRowsFromFrame(", 1)[1].split(
        "function collectCoordUniverse(", 1
    )[0]
    assert "LabReplayOverlayBucketRegistry.collectOverlayCellsForPaintTarget" in body
    assert "pushOverlayCellList(out, overlay.cells)" not in body


def test_js_overlay_registry_parity_via_node() -> None:
    node = shutil.which("node.exe" if sys.platform == "win32" else "node")
    if not node:
        pytest.skip("node not available")
    if not PARITY_SCRIPT.is_file():
        pytest.skip("parity script missing")

    proc = subprocess.run(
        [node, str(PARITY_SCRIPT)],
        cwd=str(REPO),
        input=json.dumps(PARITY_CASES).encode("utf-8"),
        capture_output=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        pytest.fail(stderr or stdout or f"exit {proc.returncode}")
