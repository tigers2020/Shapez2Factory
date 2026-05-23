from typing import Any
from unittest.mock import MagicMock

import pytest

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.dto.solver_graph import SolverShapeNode
from django_apps.shapez_solver.ports.graph_preview import NoopGraphPreviewRenderer
from django_apps.shapez_solver.services import macro_recipe_graph_visual
from django_apps.shapez_solver.services.fluid_carrier_render_scene import FLUID_CARRIER_MESH_KEY
from django_apps.shapez_solver.services.macro_recipe_graph_visual import (
    document_to_solver_graph,
    enrich_react_flow_with_macro_visual_previews,
    serialize_macro_recipe_visual,
)
from django_apps.shapez_solver.services.recipe_graph_react_flow_adapter import (
    domain_graph_to_react_flow,
)
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document
from django_apps.web.services.graph_preview import GraphPreview


def test_serialize_macro_recipe_visual_rotate_chain() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_rot",
                "kind": "operation",
                "operation": OperationType.ROTATE_CW.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_rot", "kind": "input"},
            {"from": "o_rot", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    wire = serialize_macro_recipe_visual(doc, preview_renderer=NoopGraphPreviewRenderer())
    assert wire["layout"]["direction"] == "left-to-right"
    assert len(wire["nodes"]) == 3
    assert len(wire["edges"]) == 2
    rot = next(n for n in wire["nodes"] if n["id"] == "o_rot")
    assert rot.get("x") == 200
    assert rot.get("y") == 0
    out_shape = next(n for n in wire["nodes"] if n["id"] == "s_out")
    assert out_shape["kind"] == "shape"
    assert out_shape["shape_code"] == ""


def test_serialize_macro_recipe_visual_validates_document_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """회귀 방지: 직렬화 경로에서 ``validate_graph_document``·deepcopy 이중 호출 금지."""
    calls = 0
    real_validate = macro_recipe_graph_visual.validate_graph_document

    def counting_validate(raw: object) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return real_validate(raw)

    monkeypatch.setattr(
        macro_recipe_graph_visual,
        "validate_graph_document",
        counting_validate,
    )
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_rot",
                "kind": "operation",
                "operation": OperationType.ROTATE_CW.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_rot", "kind": "input"},
            {"from": "o_rot", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    serialize_macro_recipe_visual(doc, preview_renderer=NoopGraphPreviewRenderer())
    assert calls == 1


def test_document_to_solver_graph_edges() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "a",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "x": 0,
                "y": 0,
            },
            {"id": "b", "kind": "operation", "operation": "rotate_cw", "x": 1, "y": 0},
        ],
        "edges": [{"from": "a", "to": "b", "kind": "input"}],
    }
    g = document_to_solver_graph(doc)
    assert len(g.edges) == 1
    assert g.edges[0].from_id == "a"


def test_document_to_solver_graph_painter_description_includes_color() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCu----",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "p",
                "kind": "operation",
                "operation": OperationType.PAINTER.value,
                "paint_color": "r",
                "x": 1,
                "y": 0,
            },
        ],
        "edges": [{"from": "s", "to": "p", "kind": "input"}],
    }
    g = document_to_solver_graph(doc)
    op = next(n for n in g.nodes if n.id == "p")
    assert op.kind == "operation"
    assert "paint_color=r" in op.description


def test_document_to_solver_graph_painter_description_without_paint_color_notes_fluid() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCu----",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "p",
                "kind": "operation",
                "operation": OperationType.PAINTER.value,
                "x": 1,
                "y": 0,
            },
        ],
        "edges": [{"from": "s", "to": "p", "kind": "input"}],
    }
    g = document_to_solver_graph(doc)
    op = next(n for n in g.nodes if n.id == "p")
    assert op.kind == "operation"
    assert "fluid wire" in op.description


def test_enrich_react_flow_adds_preview_scene_when_png_disabled() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "src",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "op",
                "kind": "operation",
                "operation": OperationType.ROTATE_CW.value,
                "x": 100,
                "y": 0,
            },
        ],
        "edges": [{"from": "src", "to": "op", "kind": "input"}],
    }
    v = validate_graph_document(doc)
    rf = domain_graph_to_react_flow(v)
    noop = NoopGraphPreviewRenderer()
    enriched = enrich_react_flow_with_macro_visual_previews(rf, v, preview_renderer=noop)
    src_data = next(n for n in enriched["nodes"] if n["id"] == "src").get("data") or {}
    assert src_data.get("preview_image_url") in (None, "")
    ps = src_data.get("preview_scene")
    assert isinstance(ps, dict)
    assert ps.get("normalized_code")


def test_enrich_react_flow_adds_preview_for_shapes_with_codes() -> None:
    mock_renderer = MagicMock()
    mock_renderer.render.return_value = GraphPreview(
        alt_text="Graph preview for CuCuCuCu",
        image_url="/internal/graph-preview-cache/fakecache.png",
    )
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "src",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "op",
                "kind": "operation",
                "operation": OperationType.ROTATE_CW.value,
                "x": 100,
                "y": 0,
            },
        ],
        "edges": [{"from": "src", "to": "op", "kind": "input"}],
    }
    v = validate_graph_document(doc)
    rf = domain_graph_to_react_flow(v)
    raw = next(n for n in rf["nodes"] if n["id"] == "src")
    assert "preview_image_url" not in (raw.get("data") or {})
    enriched = enrich_react_flow_with_macro_visual_previews(rf, v, preview_renderer=mock_renderer)
    src_data = next(n for n in enriched["nodes"] if n["id"] == "src").get("data") or {}
    assert isinstance(src_data.get("preview_image_url"), str)
    assert src_data["preview_image_url"].strip()


def test_enrich_react_flow_macro_visual_reuses_precomputed_serialize() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "src",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "op",
                "kind": "operation",
                "operation": OperationType.ROTATE_CW.value,
                "x": 100,
                "y": 0,
            },
        ],
        "edges": [{"from": "src", "to": "op", "kind": "input"}],
    }
    v = validate_graph_document(doc)
    rf = domain_graph_to_react_flow(v)
    noop = NoopGraphPreviewRenderer()
    visual = serialize_macro_recipe_visual(v, preview_renderer=noop)
    without_kw = enrich_react_flow_with_macro_visual_previews(rf, v, preview_renderer=noop)
    with_visual = enrich_react_flow_with_macro_visual_previews(
        rf, v, preview_renderer=noop, macro_visual=visual
    )
    assert with_visual == without_kw


def test_serialize_macro_recipe_visual_fluid_source_uses_tank_mesh() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "src_f",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "source_carrier": "fluid",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    g = document_to_solver_graph(doc)
    src_node = next(n for n in g.nodes if n.id == "src_f")
    assert isinstance(src_node, SolverShapeNode)
    assert src_node.source_carrier == "fluid"

    wire = serialize_macro_recipe_visual(doc, preview_renderer=NoopGraphPreviewRenderer())
    src = next(n for n in wire["nodes"] if n["id"] == "src_f")
    ps = src["preview_scene"]
    assert len(ps["cells"]) == 1
    assert ps["cells"][0]["mesh_key"] == FLUID_CARRIER_MESH_KEY
    assert ps["cells"][0]["shape_code"] == "t"
    assert ps["cells"][0]["material_key"] == "r"
