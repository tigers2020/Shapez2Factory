"""Parity: lab_replay_height_layer.js mirrors map_height_layer.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from django_apps.asteroid_lab.replay.map_height_layer import (
    enrich_replay_wire_row_with_layer,
    resolve_replay_height_layer,
)

REPO = Path(__file__).resolve().parents[4]
HEIGHT_JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "lab_replay_height_layer.js"
PARITY_SCRIPT = REPO / "scripts" / "run_lab_replay_height_layer_parity.mjs"

RESOLVE_CASES: list[dict[str, object]] = [
    {"cell_kind": "shape_miner", "transport_kind": "shape_belt", "expected": 0},
    {"cell_kind": "fluid_miner", "transport_kind": "fluid_pipe", "expected": 1},
    {"cell_kind": "space_belt", "transport_kind": "shape_belt", "expected": 0},
    {
        "cell_kind": "space_belt",
        "transport_kind": "space_belt",
        "tile_type": "SpaceBelt_Forward",
        "expected": 0,
    },
    {
        "cell_kind": "space_belt",
        "transport_kind": "space_belt",
        "tile_type": "SpaceBelt_Lift2UpForward",
        "expected": 1,
    },
    {"cell_kind": "space_pipe", "transport_kind": "fluid_pipe", "expected": 1},
    {
        "cell_kind": "route_probe_path",
        "transport_kind": "shape_belt",
        "expected": 0,
    },
    {
        "cell_kind": "shape_miner",
        "transport_kind": "shape_belt",
        "layer": 2,
        "expected": 2,
    },
    {
        "cell_kind": "candidate_miner",
        "transport_kind": "none",
        "output_transport_kind": "space_pipe",
        "expected": 0,
    },
    {
        "cell_kind": "candidate_miner",
        "transport_kind": "none",
        "output_transport_kind": "fluid_pipe",
        "expected": 1,
    },
]


@pytest.mark.parametrize("case", RESOLVE_CASES, ids=lambda c: str(c.get("cell_kind")))
def test_python_resolve_replay_height_layer_cases(case: dict[str, object]) -> None:
    expected = int(case["expected"])
    layer = case.get("layer")
    if case.get("output_transport_kind"):
        row = {
            "cell_kind": case.get("cell_kind"),
            "transport_kind": case.get("transport_kind"),
            "output_transport_kind": case.get("output_transport_kind"),
        }
        got = enrich_replay_wire_row_with_layer(row)["layer"]
    else:
        got = resolve_replay_height_layer(
            cell_kind=str(case.get("cell_kind") or ""),
            transport_kind=str(case.get("transport_kind") or ""),
            tile_type=str(case.get("tile_type") or ""),
            layer=int(layer) if layer is not None else None,
        )
    assert got == expected


def test_js_height_layer_module_contract() -> None:
    src = HEIGHT_JS.read_text(encoding="utf-8")
    assert "LabReplayHeightLayer" in src
    assert "function resolveReplayHeightLayer" in src
    assert "enrichReplayWireRowWithLayer" in src
    assert "wireTransportKindForLayerResolution" in src
    assert "map_height_layer.py" in src


def test_js_height_layer_parity_via_node() -> None:
    node = shutil.which("node.exe" if sys.platform == "win32" else "node")
    if not node:
        pytest.skip("node not available")
    if not PARITY_SCRIPT.is_file():
        pytest.skip("parity script missing")

    proc = subprocess.run(
        [node, str(PARITY_SCRIPT)],
        cwd=str(REPO),
        input=json.dumps(RESOLVE_CASES).encode("utf-8"),
        capture_output=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        pytest.fail(stderr or stdout or f"exit {proc.returncode}")
