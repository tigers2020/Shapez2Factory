"""graph_document(JSON) → 솔버 그래프 UI용 wire payload."""

from __future__ import annotations

import math
from typing import Any

from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverOperationNode,
    SolverShapeNode,
)
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document
from django_apps.shapez_solver.view_graph_serialization import (
    serialize_graph_edge,
    serialize_graph_node,
)
from django_apps.web.services.graph_preview import get_graph_preview_renderer


def document_to_solver_graph(doc: dict[str, Any]) -> SolverGraph:
    """검증된 graph_document를 SolverGraph DTO로 변환한다."""
    v = validate_graph_document(doc)
    nodes_out: list[SolverShapeNode | SolverOperationNode] = []
    for n in v["nodes"]:
        if n.get("kind") == "shape":
            role = str(n.get("role", "intermediate"))
            if role not in ("source", "intermediate", "target"):
                role = "intermediate"
            code = str(n.get("shape_code", "")).strip()
            nodes_out.append(
                SolverShapeNode(
                    id=str(n["id"]),
                    role=role,  # type: ignore[arg-type]
                    shape_code=code,
                    label=str(n.get("label") or n["id"]),
                    preview_scene=None,
                    quantity=int(n.get("quantity", 1)),
                )
            )
        else:
            op_key = str(n.get("operation", "")).strip()
            op_type = OperationType(op_key)
            cat = OPERATION_CATALOG[op_type]
            description = cat.description
            if op_type == OperationType.PAINTER:
                pc = str(n.get("paint_color", "")).strip()
                if pc:
                    description = f"{description} · paint_color={pc}"
            nodes_out.append(
                SolverOperationNode(
                    id=str(n["id"]),
                    operation_type=op_type.value,
                    label=cat.label,
                    icon=cat.icon,
                    input_count=cat.input_count,
                    output_count=cat.output_count,
                    description=description,
                )
            )
    edges_out: list[SolverGraphEdge] = []
    for e in v["edges"]:
        k = str(e.get("kind", ""))
        if k not in ("input", "output", "delivery"):
            continue
        edges_out.append(
            SolverGraphEdge(
                from_id=str(e["from"]),
                to_id=str(e["to"]),
                kind=k,  # type: ignore[arg-type]
                slot=e.get("slot") if isinstance(e.get("slot"), str) else None,
                label=e.get("label") if isinstance(e.get("label"), str) else None,
            )
        )
    return SolverGraph(nodes=tuple(nodes_out), edges=tuple(edges_out))


def serialize_macro_recipe_visual(doc: dict[str, Any]) -> dict[str, Any]:
    """graph_document를 ``renderSolverGraph`` / ``mountGraph``가 기대하는 JSON으로 직렬화한다."""
    v = validate_graph_document(doc)
    graph = document_to_solver_graph(doc)
    renderer = get_graph_preview_renderer()
    node_xy: dict[str, tuple[float, float]] = {}
    for n in v["nodes"]:
        nid = str(n.get("id", ""))
        if not nid:
            continue
        nx = n.get("x")
        ny = n.get("y")
        if isinstance(nx, (int, float)) and isinstance(ny, (int, float)):
            fx = float(nx)
            fy = float(ny)
            if math.isfinite(fx) and math.isfinite(fy):
                node_xy[nid] = (fx, fy)
    nodes_payload: list[dict[str, Any]] = []
    for node in graph.nodes:
        if isinstance(node, SolverShapeNode):
            if not str(node.shape_code).strip():
                payload = {
                    "id": node.id,
                    "kind": "shape",
                    "role": node.role,
                    "shape_code": "",
                    "label": node.label,
                    "quantity": node.quantity,
                    "reused_count": node.reused_count,
                }
            else:
                payload = serialize_graph_node(node, renderer)
        else:
            payload = serialize_graph_node(node, renderer)
        xy = node_xy.get(str(node.id))
        if xy is not None:
            payload["x"] = xy[0]
            payload["y"] = xy[1]
        nodes_payload.append(payload)
    return {
        "layout": {"direction": graph.direction},
        "nodes": nodes_payload,
        "edges": [serialize_graph_edge(edge) for edge in graph.edges],
    }


def enrich_react_flow_with_macro_visual_previews(
    react_flow: dict[str, Any],
    graph_doc: dict[str, Any],
) -> dict[str, Any]:
    """``domain_graph_to_react_flow`` 스냅샷에 macro visual의 미리보기 URL을 합친다."""
    nodes = react_flow.get("nodes")
    if not isinstance(nodes, list):
        return react_flow
    try:
        visual = serialize_macro_recipe_visual(graph_doc)
    except (ValueError, TypeError, KeyError):
        return react_flow
    vn = visual.get("nodes")
    if not isinstance(vn, list):
        return react_flow
    url_by_id: dict[str, tuple[str, str | None]] = {}
    for item in vn:
        if not isinstance(item, dict):
            continue
        if str(item.get("kind", "")) != "shape":
            continue
        nid = str(item.get("id") or "")
        url = item.get("preview_image_url")
        if not nid or not isinstance(url, str) or not url.strip():
            continue
        alt = item.get("preview_alt")
        url_by_id[nid] = (url.strip(), str(alt) if isinstance(alt, str) else None)
    if not url_by_id:
        return react_flow
    new_nodes: list[Any] = []
    for n in nodes:
        if not isinstance(n, dict):
            new_nodes.append(n)
            continue
        nid = str(n.get("id") or "")
        ntype = str(n.get("type") or "")
        if nid not in url_by_id or ntype not in ("shape", "intermediate"):
            new_nodes.append(n)
            continue
        url, alt = url_by_id[nid]
        data_raw = n.get("data")
        merged: dict[str, Any] = dict(data_raw) if isinstance(data_raw, dict) else {}
        merged["preview_image_url"] = url
        if alt:
            merged["preview_alt"] = alt
        new_nodes.append({**n, "data": merged})
    return {**react_flow, "nodes": new_nodes}


__all__ = [
    "document_to_solver_graph",
    "enrich_react_flow_with_macro_visual_previews",
    "serialize_macro_recipe_visual",
]
