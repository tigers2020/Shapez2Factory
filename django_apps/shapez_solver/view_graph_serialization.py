from __future__ import annotations

from typing import Any

from django.templatetags.static import static

from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_render_scene import (
    ShapeRenderScene,
    build_shape_render_scene,
)
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverGraphNode,
    SolverOperationNode,
    SolverShapeNode,
)
from django_apps.web.services.graph_preview import GraphPreviewRenderer, get_graph_preview_renderer


def serialize_solver_graph(graph: SolverGraph) -> dict[str, Any]:
    preview_renderer = get_graph_preview_renderer()
    return {
        "layout": {
            "direction": graph.direction,
        },
        "nodes": [serialize_graph_node(node, preview_renderer) for node in graph.nodes],
        "edges": [serialize_graph_edge(edge) for edge in graph.edges],
    }


def serialize_graph_node(
    node: SolverGraphNode,
    preview_renderer: GraphPreviewRenderer,
) -> dict[str, Any]:
    if isinstance(node, SolverShapeNode):
        preview_scene = node.preview_scene or build_preview_scene(node.shape_code)
        graph_preview = preview_renderer.render(preview_scene)
        payload = {
            "id": node.id,
            "kind": node.kind,
            "role": node.role,
            "shape_code": node.shape_code,
            "label": node.label,
            "quantity": node.quantity,
            "preview_scene": preview_scene,
            "preview_image_url": graph_preview.image_url,
            "preview_alt": graph_preview.alt_text,
            "reused_count": node.reused_count,
        }
        if node.produced_state is not None:
            payload["produced_state"] = node.produced_state
        if node.batch_index is not None:
            payload["batch_index"] = node.batch_index
        if node.batch_total is not None:
            payload["batch_total"] = node.batch_total
        return payload

    if isinstance(node, SolverOperationNode):
        payload = {
            "id": node.id,
            "kind": node.kind,
            "operation": {
                "type": node.operation_type,
                "label": node.label,
                "icon": static(f"web/images/operations/{node.icon}"),
                "input_count": node.input_count,
                "output_count": node.output_count,
                "description": node.description,
            },
        }
        if node.run_index is not None:
            payload["run_index"] = node.run_index
        if node.run_total is not None:
            payload["run_total"] = node.run_total
        return payload

    raise TypeError(f"Unsupported graph node: {node!r}")


def serialize_graph_edge(edge: SolverGraphEdge) -> dict[str, str | int | None]:
    return {
        "from": edge.from_id,
        "to": edge.to_id,
        "kind": edge.kind,
        "slot": edge.slot,
        "label": edge.label,
        "quantity": edge.quantity,
    }


def build_preview_scene(shape_code: str) -> dict[str, Any]:
    pattern = parse_shape_code_list(shape_code)[0]
    return serialize_render_scene(build_shape_render_scene(pattern))


def serialize_render_scene(scene: ShapeRenderScene) -> dict[str, Any]:
    return {
        "normalized_code": scene.normalized_code,
        "cells": [
            {
                "layer_index": cell.layer_index,
                "quadrant_index": cell.quadrant_index,
                "position": cell.position.value,
                "shape_code": cell.shape_code,
                "color_code": cell.color_code,
                "shape_kind": cell.shape_kind,
                "color_kind": cell.color_kind,
                "mesh_key": cell.mesh_key,
                "material_key": cell.material_key,
                "transform_key": cell.transform_key,
            }
            for cell in scene.cells
        ],
    }
