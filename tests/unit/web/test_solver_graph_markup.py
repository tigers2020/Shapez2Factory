from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any, cast

from django.conf import settings


def _run_markup_probe() -> dict[str, Any]:
    return _render_graph_markup(
        {
            "nodes": [
                {
                    "id": "shape:left",
                    "kind": "shape",
                    "role": "source",
                    "shape_code": "SuSuSuSu",
                    "label": "Source",
                    "quantity": 1,
                    "preview_image_url": "/preview/source.png",
                    "preview_alt": "Source preview",
                },
                {
                    "id": "shape:right",
                    "kind": "shape",
                    "role": "source",
                    "shape_code": "CuCuCuCu",
                    "label": "Source",
                    "quantity": 1,
                    "preview_image_url": "/preview/source-b.png",
                    "preview_alt": "Source preview B",
                },
                {
                    "id": "op:stacker",
                    "kind": "operation",
                    "operation": {
                        "label": "Stacker",
                        "icon": "/static/web/images/operations/stacker.png",
                        "input_count": 2,
                        "output_count": 1,
                    },
                },
                {
                    "id": "shape:target",
                    "kind": "shape",
                    "role": "target",
                    "shape_code": "CuRuSuWu",
                    "label": "Target x4",
                    "quantity": 4,
                    "preview_image_url": "/preview/target.png",
                    "preview_alt": "Target preview",
                    "batch_index": 3,
                    "batch_total": 4,
                },
            ],
            "edges": [
                {
                    "from": "shape:left",
                    "to": "op:stacker",
                    "kind": "input",
                    "slot": "Input A",
                    "label": "Input A",
                },
                {
                    "from": "shape:right",
                    "to": "op:stacker",
                    "kind": "input",
                    "slot": "Input B",
                    "label": "Input B",
                },
                {
                    "from": "op:stacker",
                    "to": "shape:target",
                    "kind": "output",
                    "slot": "Output A",
                    "label": "Output A",
                },
            ],
        }
    )


def _render_graph_markup(graph: dict[str, object]) -> dict[str, Any]:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web" / "js"
    module_url = (static_root / "solver_timeline" / "graph_markup.js").as_uri()
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".json",
        delete=False,
    ) as handle:
        json.dump(graph, handle)
        graph_json_path = handle.name
    script = textwrap.dedent(f"""
        import fs from "node:fs";
        import {{ computeEdgeGeometry, renderSolverGraph }} from "{module_url}";

        const graph = JSON.parse(fs.readFileSync({json.dumps(graph_json_path)}, "utf8"));

        const inputANode = {{
          id: "shape:left",
          kind: "shape",
          position: {{ x: 40, y: 40 }},
        }};
        const inputBNode = {{
          id: "shape:right",
          kind: "shape",
          position: {{ x: 40, y: 400 }},
        }};
        const operationNode = {{
          id: "op:stacker",
          kind: "operation",
          operation: {{
            input_count: 2,
            output_count: 1,
          }},
          position: {{ x: 420, y: 220 }},
        }};

        const geometryA = computeEdgeGeometry(
          graph.edges[0],
          inputANode,
          operationNode,
          0,
        );
        const geometryB = computeEdgeGeometry(
          graph.edges[1],
          inputBNode,
          operationNode,
          1,
        );

        console.log(JSON.stringify({{
          html: renderSolverGraph(graph),
          geometryA,
          geometryB,
        }}));
        """).strip()
    try:
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=settings.BASE_DIR,
        )
        return cast(dict[str, Any], json.loads(completed.stdout))
    finally:
        Path(graph_json_path).unlink(missing_ok=True)


def test_graph_markup_uses_fixed_shape_cards_without_scrollbars() -> None:
    payload = _run_markup_probe()
    html = payload["html"]

    assert "overflow-y-auto" not in html
    assert "overflow-hidden" in html
    assert "height: 104px;" in html


def test_graph_markup_uses_elbow_line_segments_instead_of_bezier_curves() -> None:
    payload = _run_markup_probe()
    html = payload["html"]

    assert 'marker-end="url(#arrowhead)"' in html
    assert " L " in html
    assert " C " not in html


def test_graph_markup_separates_multi_input_ports_by_lane() -> None:
    payload = _run_markup_probe()
    geometry_a = payload["geometryA"]
    geometry_b = payload["geometryB"]

    assert geometry_a["y2"] != geometry_b["y2"]
    assert geometry_a["elbowX"] != geometry_b["elbowX"]
    assert geometry_a["labelY"] != geometry_b["labelY"]


def test_solver_graph_payload_renders_with_current_graph_markup() -> None:
    from django.test import Client

    response = Client().post("/api/solver/solve/", data={"code": "RcCuRcCu"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["found"] is True
    graph = payload["graph"]
    assert graph is not None

    rendered = _render_graph_markup(cast(dict[str, object], graph))
    html = rendered["html"]

    assert "overflow-y-auto" not in html
    assert " C " not in html
    assert "data-graph-edge-label" in html
