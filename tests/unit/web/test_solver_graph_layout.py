from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import cast

from django.conf import settings


def _run_layout(graph: dict[str, object]) -> dict[str]:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web" / "js"
    module_url = (static_root / "solver_graph_layout.js").as_uri()
    script = textwrap.dedent(f"""
        import {{ COLUMN_GAP, computeGraphLayout, NODE_HEIGHT, NODE_WIDTH }} from "{module_url}";

        const graph = {json.dumps(graph)};
        const layout = computeGraphLayout(graph);
        const positions = Object.fromEntries(
          [...layout.positions.entries()].map(([nodeId, position]) => [nodeId, position]),
        );

        console.log(JSON.stringify({{
          positions,
          width: layout.width,
          height: layout.height,
          bounds: layout.bounds,
          columnGap: COLUMN_GAP,
          nodeHeight: NODE_HEIGHT,
          nodeWidth: NODE_WIDTH,
        }}));
        """).strip()
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        cwd=settings.BASE_DIR,
    )
    return cast(dict[str], json.loads(completed.stdout))


def _sample_graph() -> dict[str, object]:
    return {
        "nodes": [
            {"id": "shape:c", "kind": "shape"},
            {"id": "shape:a", "kind": "shape"},
            {"id": "shape:b", "kind": "shape"},
            {"id": "op:a", "kind": "operation"},
            {"id": "op:c", "kind": "operation"},
            {"id": "op:b", "kind": "operation"},
            {"id": "shape:ab-left", "kind": "shape"},
            {"id": "shape:c-mid", "kind": "shape"},
            {"id": "shape:ab-right", "kind": "shape"},
            {"id": "op:join", "kind": "operation"},
            {"id": "op:solo", "kind": "operation"},
            {"id": "shape:target", "kind": "shape"},
            {"id": "shape:side-target", "kind": "shape"},
        ],
        "edges": [
            {"from": "shape:a", "to": "op:a"},
            {"from": "op:a", "to": "shape:ab-left"},
            {"from": "shape:b", "to": "op:b"},
            {"from": "op:b", "to": "shape:ab-right"},
            {"from": "shape:c", "to": "op:c"},
            {"from": "op:c", "to": "shape:c-mid"},
            {"from": "shape:ab-left", "to": "op:join"},
            {"from": "shape:ab-right", "to": "op:join"},
            {"from": "op:join", "to": "shape:target"},
            {"from": "shape:c-mid", "to": "op:solo"},
            {"from": "op:solo", "to": "shape:side-target"},
        ],
    }


def _late_merge_graph() -> dict[str, object]:
    return {
        "nodes": [
            {"id": "shape:left-start", "kind": "shape"},
            {"id": "shape:right-start", "kind": "shape"},
            {"id": "op:left-a", "kind": "operation"},
            {"id": "op:right-a", "kind": "operation"},
            {"id": "shape:left-mid", "kind": "shape"},
            {"id": "shape:right-mid", "kind": "shape"},
            {"id": "op:left-b", "kind": "operation"},
            {"id": "op:right-b", "kind": "operation"},
            {"id": "shape:left-end", "kind": "shape"},
            {"id": "shape:right-end", "kind": "shape"},
            {"id": "op:join", "kind": "operation"},
            {"id": "shape:target", "kind": "shape"},
        ],
        "edges": [
            {"from": "shape:left-start", "to": "op:left-a"},
            {"from": "op:left-a", "to": "shape:left-mid"},
            {"from": "shape:left-mid", "to": "op:left-b"},
            {"from": "op:left-b", "to": "shape:left-end"},
            {"from": "shape:right-start", "to": "op:right-a"},
            {"from": "op:right-a", "to": "shape:right-mid"},
            {"from": "shape:right-mid", "to": "op:right-b"},
            {"from": "op:right-b", "to": "shape:right-end"},
            {"from": "shape:left-end", "to": "op:join"},
            {"from": "shape:right-end", "to": "op:join"},
            {"from": "op:join", "to": "shape:target"},
        ],
    }


def test_grouped_layout_keeps_join_branches_closer_than_unrelated_branch() -> None:
    layout = _run_layout(_sample_graph())
    positions = layout["positions"]

    join_gap = abs(positions["op:a"]["y"] - positions["op:b"]["y"])
    unrelated_gap = abs(positions["op:a"]["y"] - positions["op:c"]["y"])

    assert join_gap < unrelated_gap


def test_grouped_layout_is_deterministic_for_same_graph() -> None:
    graph = _sample_graph()

    first = _run_layout(graph)
    second = _run_layout(graph)

    assert first == second


def test_grouped_layout_does_not_keep_same_depth_nodes_on_uniform_row_grid() -> None:
    layout = _run_layout(_sample_graph())
    positions = layout["positions"]

    ordered_y = sorted(positions[node_id]["y"] for node_id in ("shape:c", "shape:a", "shape:b"))
    gaps = [
        round(ordered_y[index + 1] - ordered_y[index], 4) for index in range(len(ordered_y) - 1)
    ]

    assert len(set(gaps)) > 1


def test_grouped_layout_keeps_every_edge_moving_left_to_right() -> None:
    graph = _late_merge_graph()
    layout = _run_layout(graph)
    positions = layout["positions"]
    node_width = layout["nodeWidth"]
    edges = cast(list[dict[str, str]], graph["edges"])

    for edge in edges:
        assert positions[edge["to"]]["x"] >= positions[edge["from"]]["x"] + node_width


def test_grouped_layout_spreads_late_merge_branches_horizontally() -> None:
    layout = _run_layout(_late_merge_graph())
    positions = layout["positions"]

    assert positions["shape:left-mid"]["x"] != positions["shape:right-mid"]["x"]
    assert positions["op:left-b"]["x"] != positions["op:right-b"]["x"]


def test_grouped_layout_right_aligns_same_depth_terminal_nodes() -> None:
    layout = _run_layout(_sample_graph())
    positions = layout["positions"]

    assert (
        positions["shape:target"]["x"] - positions["shape:side-target"]["x"] == layout["columnGap"]
    )


def test_grouped_layout_bounds_cover_all_node_boxes() -> None:
    layout = _run_layout(_sample_graph())
    positions = layout["positions"]
    bounds = layout["bounds"]
    node_height = layout["nodeHeight"]
    node_width = layout["nodeWidth"]

    assert bounds["width"] > 0
    assert bounds["height"] > 0

    for position in positions.values():
        assert bounds["minX"] <= position["x"] <= bounds["maxX"] - node_width
        assert bounds["minY"] <= position["y"] <= bounds["maxY"] - node_height
