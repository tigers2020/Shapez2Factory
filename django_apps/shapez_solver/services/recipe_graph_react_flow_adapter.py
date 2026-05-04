"""graph_document(JSON) ↔ React Flow(@xyflow/react) 초기 요소 스냅샷 어댑터.

브라우저 편집기는 React Flow 전용 필드(노드 ``type``, 엣지 ``source``/``target`` 등)를
쓰고, 저장·재계산 계약은 ``graph_document``를 유지한다. 본 모듈은 그 사이의
직렬화 가능한 JSON 스냅샷을 정의한다.

프론트엔드는 동일 스키마의 ``react_flow_initial`` 객체를 부트스트랩으로 받아
초기 노드·엣지로 주입한다(단일 권위: 서버 변환).
"""

from __future__ import annotations

from typing import Any, Literal

from django_apps.shapez_solver.services.recipe_graph_constants import RECIPE_GRAPH_SCHEMA_VERSION

REACT_FLOW_GRAPH_PAYLOAD_VERSION = 1

RfNodeType = Literal["shape", "operation", "intermediate", "output"]


def _nodes_raw_to_rf(nodes_raw: list[Any]) -> list[dict[str, Any]]:
    rf_nodes: list[dict[str, Any]] = []
    for n in nodes_raw:
        if not isinstance(n, dict):
            raise ValueError("each node must be an object")
        rf_nodes.append(_domain_node_to_rf(n))
    return rf_nodes


def _edges_raw_to_rf(edges_raw: list[Any]) -> list[dict[str, Any]]:
    rf_edges: list[dict[str, Any]] = []
    for e in edges_raw:
        if not isinstance(e, dict):
            raise ValueError("each edge must be an object")
        rf_edges.append(_domain_edge_to_rf(e))
    return rf_edges


def _annotate_rf_edges_for_react_flow(
    rf_edges: list[dict[str, Any]], edges_raw: list[Any]
) -> None:
    input_counts: dict[str, int] = {}
    for ed, raw in zip(rf_edges, edges_raw, strict=True):
        if not isinstance(raw, dict):
            continue
        ek = raw.get("kind")
        if ek == "input":
            tid = str(raw["to"])
            idx = input_counts.get(tid, 0)
            input_counts[tid] = idx + 1
            if idx > 0:
                ed["targetHandle"] = f"in-{idx}"
        elif ek in ("output", "delivery"):
            ed["sourceHandle"] = "out"
            ed["targetHandle"] = "in"
        ed["type"] = "recipe"


def domain_graph_to_react_flow(graph_document: dict[str, Any]) -> dict[str, Any]:
    """검증된 ``graph_document``를 React Flow 초기 요소 스냅샷으로 변환한다."""
    nodes_raw = graph_document.get("nodes")
    edges_raw = graph_document.get("edges")
    if not isinstance(nodes_raw, list) or not isinstance(edges_raw, list):
        raise ValueError("graph_document nodes/edges must be lists")
    rf_nodes = _nodes_raw_to_rf(nodes_raw)
    rf_edges = _edges_raw_to_rf(edges_raw)
    _annotate_rf_edges_for_react_flow(rf_edges, edges_raw)
    return {
        "version": REACT_FLOW_GRAPH_PAYLOAD_VERSION,
        "nodes": rf_nodes,
        "edges": rf_edges,
    }


def react_flow_to_domain_graph(payload: dict[str, Any]) -> dict[str, Any]:
    """스냅샷을 ``graph_document`` 형태로 복원한다(저장 직전 검증은 호출 측)."""
    version = payload.get("version")
    if version is not None and int(version) != REACT_FLOW_GRAPH_PAYLOAD_VERSION:
        raise ValueError(f"unsupported react flow payload version: {version}")
    rf_nodes = payload.get("nodes")
    rf_edges = payload.get("edges")
    if not isinstance(rf_nodes, list) or not isinstance(rf_edges, list):
        raise ValueError("payload nodes/edges must be lists")
    domain_nodes: list[dict[str, Any]] = []
    for rn in rf_nodes:
        if not isinstance(rn, dict):
            raise ValueError("each react flow node must be an object")
        domain_nodes.append(_rf_node_to_domain(rn))
    domain_edges: list[dict[str, Any]] = []
    for re in rf_edges:
        if not isinstance(re, dict):
            raise ValueError("each react flow edge must be an object")
        domain_edges.append(_rf_edge_to_domain(re))
    return {
        "schema_version": RECIPE_GRAPH_SCHEMA_VERSION,
        "nodes": domain_nodes,
        "edges": domain_edges,
    }


def _domain_node_to_rf_type(node: dict[str, Any]) -> RfNodeType:
    kind = node.get("kind")
    if kind == "operation":
        return "operation"
    if kind != "shape":
        raise ValueError(f"invalid node kind: {kind}")
    role = str(node.get("role", "intermediate"))
    if role == "source":
        return "shape"
    if role == "target":
        return "output"
    if role == "intermediate":
        return "intermediate"
    raise ValueError(f"invalid shape role for react flow: {role}")


def _domain_node_to_rf(node: dict[str, Any]) -> dict[str, Any]:
    nid = str(node["id"])
    ntype = _domain_node_to_rf_type(node)
    x = float(node.get("x", 0.0))
    y = float(node.get("y", 0.0))
    data: dict[str, Any]
    if node.get("kind") == "operation":
        data = {"operation": str(node["operation"])}
        if "paint_color" in node and node["paint_color"] is not None:
            data["paint_color"] = str(node["paint_color"])
    else:
        data = {
            "shape_code": str(node.get("shape_code", "")),
            "quantity": int(node.get("quantity", 1) or 1),
            "role": str(node.get("role", "intermediate")),
        }
    return {"id": nid, "type": ntype, "position": {"x": x, "y": y}, "data": data}


def _domain_edge_to_rf(edge: dict[str, Any]) -> dict[str, Any]:
    ek = edge.get("kind")
    if ek not in ("input", "output", "delivery"):
        raise ValueError(f"invalid edge kind: {ek!r}")
    src = str(edge["from"])
    tgt = str(edge["to"])
    eid = f"e-{src}-{tgt}-{ek}"
    data: dict[str, Any] = {"domainKind": ek}
    if edge.get("slot") is not None:
        data["slot"] = str(edge["slot"])
    return {"id": eid, "source": src, "target": tgt, "data": data}


def _rf_node_to_domain(rf: dict[str, Any]) -> dict[str, Any]:
    nid = str(rf["id"])
    ntype = str(rf.get("type", ""))
    pos_raw = rf.get("position")
    pos: dict[str, Any] = pos_raw if isinstance(pos_raw, dict) else {}
    x = float(pos.get("x", 0.0))
    y = float(pos.get("y", 0.0))
    data_raw = rf.get("data")
    data: dict[str, Any] = data_raw if isinstance(data_raw, dict) else {}
    if ntype == "operation":
        out: dict[str, Any] = {
            "id": nid,
            "kind": "operation",
            "operation": str(data["operation"]),
            "x": x,
            "y": y,
        }
        if "paint_color" in data:
            out["paint_color"] = str(data["paint_color"])
        return out
    role_map = {"shape": "source", "intermediate": "intermediate", "output": "target"}
    if ntype not in role_map:
        raise ValueError(f"unsupported react flow node type: {ntype}")
    role = role_map[ntype]
    return {
        "id": nid,
        "kind": "shape",
        "role": role,
        "shape_code": str(data.get("shape_code", "")),
        "quantity": int(data.get("quantity", 1) or 1),
        "x": x,
        "y": y,
    }


def _rf_edge_to_domain(rf: dict[str, Any]) -> dict[str, Any]:
    data_raw = rf.get("data")
    data: dict[str, Any] = data_raw if isinstance(data_raw, dict) else {}
    kind = data.get("domainKind")
    if kind not in ("input", "output", "delivery"):
        raise ValueError("react flow edge missing data.domainKind")
    out: dict[str, Any] = {
        "from": str(rf["source"]),
        "to": str(rf["target"]),
        "kind": kind,
    }
    if kind == "input":
        th = rf.get("targetHandle")
        if isinstance(th, str) and th.startswith("in-") and len(th) > 3:
            suffix = th[3:]
            if suffix.isdigit() and int(suffix) >= 1:
                out["slot"] = suffix
    if "slot" in data and "slot" not in out:
        out["slot"] = str(data["slot"])
    return out


__all__ = [
    "REACT_FLOW_GRAPH_PAYLOAD_VERSION",
    "domain_graph_to_react_flow",
    "react_flow_to_domain_graph",
]
