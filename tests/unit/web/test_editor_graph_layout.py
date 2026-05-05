from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any, cast

from django.conf import settings


def _run_editor_layout(graph: dict[str, object]) -> dict[str, Any]:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web" / "js"
    module_url = (static_root / "editor_graph_layout.js").as_uri()
    script = textwrap.dedent(f"""
        import {{ computeEditorGraphLayout }} from "{module_url}";

        const graph = {json.dumps(graph)};
        const layout = computeEditorGraphLayout(graph);
        const positions = Object.fromEntries(
          [...layout.positions.entries()].map(([nodeId, position]) => [nodeId, position]),
        );

        console.log(JSON.stringify({{ positions, width: layout.width, height: layout.height }}));
        """).strip()
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        cwd=settings.BASE_DIR,
    )
    return cast(dict[str, Any], json.loads(completed.stdout))


def test_editor_two_source_painter_between_sources_vertically() -> None:
    """Merge op stays vertically between predecessor sources (no downward merge bias)."""
    graph: dict[str, object] = {
        "nodes": [
            {"id": "mat", "layerSortKey": 40, "reactFlowType": "shape"},
            {"id": "flu", "layerSortKey": 100, "reactFlowType": "shape"},
            {"id": "paint", "layerSortKey": 0, "reactFlowType": "operation"},
        ],
        "edges": [
            {
                "from": "mat",
                "to": "paint",
                "targetHandle": "in",
                "targetPortVisualRank": 1,
            },
            {
                "from": "flu",
                "to": "paint",
                "targetHandle": "in-1",
                "targetPortVisualRank": 0,
            },
        ],
    }
    out = _run_editor_layout(graph)
    positions = out["positions"]
    mat_y = positions["mat"]["y"]
    flu_y = positions["flu"]["y"]
    paint_y = positions["paint"]["y"]
    low = min(mat_y, flu_y)
    high = max(mat_y, flu_y)
    assert low <= paint_y <= high, (
        f"painter y should lie between source ys: paint_y={paint_y} range=[{low},{high}]"
    )


def test_editor_layout_deterministic() -> None:
    graph: dict[str, object] = {
        "nodes": [
            {"id": "a", "layerSortKey": 0, "reactFlowType": "shape"},
            {"id": "b", "layerSortKey": 100, "reactFlowType": "shape"},
            {"id": "op", "layerSortKey": 0, "reactFlowType": "operation"},
        ],
        "edges": [
            {"from": "a", "to": "op"},
            {"from": "b", "to": "op"},
        ],
    }
    first = _run_editor_layout(graph)
    second = _run_editor_layout(graph)
    assert first["positions"] == second["positions"]


def test_editor_preserves_initial_y_within_same_depth() -> None:
    """Same depth + same layerSortKey: smaller initialY stays above (smaller layout y)."""
    graph: dict[str, object] = {
        "nodes": [
            {"id": "upper", "layerSortKey": 50, "reactFlowType": "shape", "initialY": 12.0},
            {"id": "lower", "layerSortKey": 50, "reactFlowType": "shape", "initialY": 900.0},
        ],
        "edges": [],
    }
    out = _run_editor_layout(graph)
    positions = out["positions"]
    assert positions["upper"]["y"] < positions["lower"]["y"]


def test_editor_dual_output_handles_top_above_bottom() -> None:
    """Cutter `out` branch lays out above `out-1` when initialY matches that intent."""
    graph: dict[str, object] = {
        "nodes": [
            {"id": "cut", "layerSortKey": 0, "reactFlowType": "operation"},
            {
                "id": "top_shape",
                "layerSortKey": 0,
                "reactFlowType": "intermediate",
                "initialY": 0.0,
            },
            {
                "id": "bot_shape",
                "layerSortKey": 0,
                "reactFlowType": "intermediate",
                "initialY": 400.0,
            },
        ],
        "edges": [
            {"from": "cut", "to": "top_shape", "sourceHandle": "out", "targetHandle": "in"},
            {"from": "cut", "to": "bot_shape", "sourceHandle": "out-1", "targetHandle": "in"},
        ],
    }
    out = _run_editor_layout(graph)
    positions = out["positions"]
    assert positions["top_shape"]["y"] < positions["bot_shape"]["y"]


def test_editor_painter_merge_port_rank_orders_above_initial_y() -> None:
    """in-1 (upper port) aligns above in even when initialY has the sources swapped."""
    graph: dict[str, object] = {
        "nodes": [
            {"id": "to_in", "layerSortKey": 40, "reactFlowType": "shape", "initialY": 0.0},
            {"id": "to_in1", "layerSortKey": 40, "reactFlowType": "shape", "initialY": 800.0},
            {"id": "paint", "layerSortKey": 0, "reactFlowType": "operation"},
        ],
        "edges": [
            {
                "from": "to_in",
                "to": "paint",
                "targetHandle": "in",
                "targetPortVisualRank": 1,
            },
            {
                "from": "to_in1",
                "to": "paint",
                "targetHandle": "in-1",
                "targetPortVisualRank": 0,
            },
        ],
    }
    out = _run_editor_layout(graph)
    pos = out["positions"]
    assert pos["to_in1"]["y"] < pos["to_in"]["y"]
