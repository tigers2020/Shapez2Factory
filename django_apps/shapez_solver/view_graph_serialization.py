from __future__ import annotations

from typing import Any

from django.templatetags.static import static

from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_render_scene import (
    build_shape_render_scene,
    serialize_render_scene,
)
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverGraphNode,
    SolverOperationNode,
    SolverShapeNode,
)
from django_apps.shapez_solver.ports.graph_preview import GraphPreviewRenderer
from django_apps.shapez_solver.services.fluid_carrier_render_scene import (
    build_fluid_carrier_preview_scene,
)


def serialize_solver_graph(
    graph: SolverGraph,
    preview_renderer: GraphPreviewRenderer,
) -> dict[str, Any]:
    return {
        "layout": {
            "direction": graph.direction,
        },
        "nodes": [
            serialize_graph_node(node, preview_renderer, sync_png=True) for node in graph.nodes
        ],
        "edges": [serialize_graph_edge(edge) for edge in graph.edges],
    }


def _serialize_solver_shape_node(
    node: SolverShapeNode,
    preview_renderer: GraphPreviewRenderer,
    *,
    sync_png: bool,
) -> dict[str, Any]:
    preview_scene = node.preview_scene or build_preview_scene(
        node.shape_code,
        source_carrier=node.source_carrier,
    )
    graph_preview = (
        preview_renderer.render(preview_scene)
        if sync_png
        else preview_renderer.render_cached_only(preview_scene)
    )
    payload: dict[str, Any] = {
        "id": node.id,
        "kind": node.kind,
        "role": node.role,
        "shape_code": node.shape_code,
        "label": node.label,
        "quantity": node.quantity,
        "preview_scene": preview_scene,
        "preview_alt": graph_preview.alt_text,
        "reused_count": node.reused_count,
    }
    if sync_png or graph_preview.image_url:
        payload["preview_image_url"] = graph_preview.image_url
    # Omit needs_warm / preview_cache_key: macro graph tiles compose sprites from
    # preview_scene client-side; server-side Playwright warm was blocking page loads.
    if node.produced_state is not None:
        payload["produced_state"] = node.produced_state
    if node.batch_index is not None:
        payload["batch_index"] = node.batch_index
    if node.batch_total is not None:
        payload["batch_total"] = node.batch_total
    return payload


def _serialize_solver_operation_node(node: SolverOperationNode) -> dict[str, Any]:
    payload: dict[str, Any] = {
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


def serialize_graph_node(
    node: SolverGraphNode,
    preview_renderer: GraphPreviewRenderer,
    *,
    sync_png: bool = True,
) -> dict[str, Any]:
    if isinstance(node, SolverShapeNode):
        return _serialize_solver_shape_node(node, preview_renderer, sync_png=sync_png)
    if isinstance(node, SolverOperationNode):
        return _serialize_solver_operation_node(node)
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


def build_preview_scene(shape_code: str, *, source_carrier: str | None = None) -> dict[str, Any]:
    pattern = parse_shape_code_list(shape_code)[0]
    if source_carrier == "fluid":
        scene = build_fluid_carrier_preview_scene(pattern)
    else:
        scene = build_shape_render_scene(pattern)
    return serialize_render_scene(scene)
