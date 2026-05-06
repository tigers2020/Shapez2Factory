"""graph_document(JSON) → 솔버 그래프 UI용 wire payload."""

from __future__ import annotations

import math
from typing import Any, Literal

from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverOperationNode,
    SolverShapeNode,
)
from django_apps.shapez_solver.ports.graph_preview import GraphPreviewRenderer
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document
from django_apps.shapez_solver.view_graph_serialization import (
    serialize_graph_edge,
    serialize_graph_node,
)


def _normalize_shape_role(role_raw: Any) -> str:
    role = str(role_raw or "intermediate")
    if role in ("source", "intermediate", "target"):
        return role
    return "intermediate"


def _graph_node_doc_to_solver(n: dict[str, Any]) -> SolverShapeNode | SolverOperationNode:
    if n.get("kind") == "shape":
        role = _normalize_shape_role(n.get("role"))
        code = str(n.get("shape_code", "")).strip()
        raw_carrier = n.get("source_carrier")
        carrier: Literal["fluid"] | None = None
        if isinstance(raw_carrier, str) and raw_carrier.strip() == "fluid":
            carrier = "fluid"
        return SolverShapeNode(
            id=str(n["id"]),
            role=role,  # type: ignore[arg-type]
            shape_code=code,
            label=str(n.get("label") or n["id"]),
            preview_scene=None,
            quantity=int(n.get("quantity", 1)),
            source_carrier=carrier,
        )
    op_key = str(n.get("operation", "")).strip()
    op_type = OperationType(op_key)
    cat = OPERATION_CATALOG[op_type]
    description = cat.description
    if op_type == OperationType.PAINTER:
        pc = str(n.get("paint_color", "")).strip()
        if pc:
            description = f"{description} · paint_color={pc}"
        else:
            description = f"{description} · fluid wire (upper port in-1) + shape (lower port in)"
    elif op_type == OperationType.CRYSTAL_GENERATOR:
        cc = str(n.get("crystal_color", "")).strip()
        if cc:
            description = f"{description} · crystal_color={cc}"
        else:
            description = f"{description} · fluid wire (upper port in-1) + shape (lower port in)"
    return SolverOperationNode(
        id=str(n["id"]),
        operation_type=op_type.value,
        label=cat.label,
        icon=cat.icon,
        input_count=cat.input_count,
        output_count=cat.output_count,
        description=description,
    )


def _edge_doc_to_solver_edge(e: dict[str, Any]) -> SolverGraphEdge | None:
    k = str(e.get("kind", ""))
    if k not in ("input", "output", "delivery"):
        return None
    return SolverGraphEdge(
        from_id=str(e["from"]),
        to_id=str(e["to"]),
        kind=k,  # type: ignore[arg-type]
        slot=e.get("slot") if isinstance(e.get("slot"), str) else None,
        label=e.get("label") if isinstance(e.get("label"), str) else None,
    )


def _solver_graph_from_validated_document(v: dict[str, Any]) -> SolverGraph:
    """``validate_graph_document`` 결과 dict만 받는다(추가 검증·deepcopy 없음)."""
    nodes_out = [_graph_node_doc_to_solver(n) for n in v["nodes"]]
    edges_out: list[SolverGraphEdge] = []
    for e in v["edges"]:
        edge = _edge_doc_to_solver_edge(e)
        if edge is not None:
            edges_out.append(edge)
    return SolverGraph(nodes=tuple(nodes_out), edges=tuple(edges_out))


def document_to_solver_graph(doc: dict[str, Any]) -> SolverGraph:
    """graph_document JSON을 검증한 뒤 SolverGraph DTO로 변환한다."""
    v = validate_graph_document(doc)
    return _solver_graph_from_validated_document(v)


def _collect_node_xy(nodes: list[Any]) -> dict[str, tuple[float, float]]:
    node_xy: dict[str, tuple[float, float]] = {}
    for n in nodes:
        nid = str(n.get("id", ""))
        if not nid:
            continue
        nx = n.get("x")
        ny = n.get("y")
        if not isinstance(nx, (int, float)) or not isinstance(ny, (int, float)):
            continue
        fx = float(nx)
        fy = float(ny)
        if not math.isfinite(fx) or not math.isfinite(fy):
            continue
        node_xy[nid] = (fx, fy)
    return node_xy


def _macro_payload_for_node(
    node: SolverShapeNode | SolverOperationNode,
    renderer: GraphPreviewRenderer,
    *,
    sync_png: bool = True,
) -> dict[str, Any]:
    if isinstance(node, SolverShapeNode) and not str(node.shape_code).strip():
        return {
            "id": node.id,
            "kind": "shape",
            "role": node.role,
            "shape_code": "",
            "label": node.label,
            "quantity": node.quantity,
            "reused_count": node.reused_count,
        }
    return serialize_graph_node(node, renderer, sync_png=sync_png)


def serialize_macro_recipe_visual(
    doc: dict[str, Any],
    *,
    sync_png: bool = True,
    preview_renderer: GraphPreviewRenderer,
) -> dict[str, Any]:
    """graph_document를 ``renderSolverGraph`` / ``mountGraph``가 기대하는 JSON으로 직렬화한다."""
    v = validate_graph_document(doc)
    graph = _solver_graph_from_validated_document(v)
    node_xy = _collect_node_xy(v["nodes"])
    nodes_payload: list[dict[str, Any]] = []
    for node in graph.nodes:
        payload = _macro_payload_for_node(node, preview_renderer, sync_png=sync_png)
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


def _load_macro_visual_payload(
    graph_doc: dict[str, Any],
    macro_visual: dict[str, Any] | None,
    preview_renderer: GraphPreviewRenderer,
) -> dict[str, Any] | None:
    try:
        if isinstance(macro_visual, dict):
            return macro_visual
        return serialize_macro_recipe_visual(graph_doc, preview_renderer=preview_renderer)
    except (ValueError, TypeError, KeyError):
        return None


def _build_shape_overlay_entry_fields(item: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {}
    ps = item.get("preview_scene")
    if isinstance(ps, dict):
        entry["preview_scene"] = ps
    url = item.get("preview_image_url")
    if isinstance(url, str) and url.strip():
        entry["preview_image_url"] = url.strip()
    alt = item.get("preview_alt")
    if isinstance(alt, str) and alt.strip():
        entry["preview_alt"] = alt.strip()
    ck = item.get("preview_cache_key")
    if isinstance(ck, str) and ck.strip():
        entry["preview_cache_key"] = ck.strip()
    if item.get("needs_warm") is True:
        entry["needs_warm"] = True
    return entry


def _shape_overlay_pair_from_visual_item(
    item: dict[str, Any],
) -> tuple[str, dict[str, Any]] | None:
    if str(item.get("kind", "")) != "shape":
        return None
    nid = str(item.get("id") or "")
    if not nid:
        return None
    entry = _build_shape_overlay_entry_fields(item)
    if not entry:
        return None
    return (nid, entry)


def _shape_visual_overlay_by_node_id(
    visual: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Wire 노드(kind=shape)의 PNG URL·scene·alt를 React 노드 id 기준으로 묶는다."""
    vn = visual.get("nodes")
    if not isinstance(vn, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in vn:
        if not isinstance(item, dict):
            continue
        pair = _shape_overlay_pair_from_visual_item(item)
        if pair is None:
            continue
        nid, entry = pair
        out[nid] = entry
    return out


def _merge_preview_into_react_node(
    n: dict[str, Any],
    overlay_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    nid = str(n.get("id") or "")
    ntype = str(n.get("type") or "")
    if nid not in overlay_by_id or ntype not in ("shape", "intermediate", "output"):
        return n
    overlay = overlay_by_id[nid]
    data_raw = n.get("data")
    merged: dict[str, Any] = dict(data_raw) if isinstance(data_raw, dict) else {}
    if "preview_scene" in overlay:
        merged["preview_scene"] = overlay["preview_scene"]
    if "preview_image_url" in overlay:
        merged["preview_image_url"] = overlay["preview_image_url"]
    elif "preview_scene" in overlay:
        merged.pop("preview_image_url", None)
    if "preview_alt" in overlay:
        merged["preview_alt"] = overlay["preview_alt"]
    if "preview_cache_key" in overlay:
        merged["preview_cache_key"] = overlay["preview_cache_key"]
    if "needs_warm" in overlay:
        merged["needs_warm"] = overlay["needs_warm"]
    return {**n, "data": merged}


def enrich_react_flow_with_macro_visual_previews(
    react_flow: dict[str, Any],
    graph_doc: dict[str, Any],
    *,
    preview_renderer: GraphPreviewRenderer,
    macro_visual: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """React Flow 스냅샷에 macro visual 미리보기(PNG URL, preview_scene, alt)를 합친다."""
    nodes = react_flow.get("nodes")
    if not isinstance(nodes, list):
        return react_flow
    visual = _load_macro_visual_payload(graph_doc, macro_visual, preview_renderer)
    if visual is None:
        return react_flow
    overlay_by_id = _shape_visual_overlay_by_node_id(visual)
    if not overlay_by_id:
        return react_flow
    new_nodes: list[Any] = []
    for n in nodes:
        if not isinstance(n, dict):
            new_nodes.append(n)
            continue
        new_nodes.append(_merge_preview_into_react_node(n, overlay_by_id))
    return {**react_flow, "nodes": new_nodes}


__all__ = [
    "document_to_solver_graph",
    "enrich_react_flow_with_macro_visual_previews",
    "serialize_macro_recipe_visual",
    "validate_graph_document",
]
