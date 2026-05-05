"""Recipe graph document: validate, topo order, and engine-backed recompute."""

from __future__ import annotations

import copy
import uuid
from collections import defaultdict, deque
from typing import Any

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.operation_semantics import apply_operation
from django_apps.shapez_solver.services.recipe_graph_constants import (
    RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING,
    RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS,
    RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING,
    RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET,
    RECIPE_GRAPH_ENGINE_OPERATIONS,
    RECIPE_GRAPH_SCHEMA_VERSION,
)
from django_apps.shapez_solver.services.recipe_graph_topology import (
    assert_delivery_targets_unique,
    assert_recipe_graph_edge_topology,
    index_recipe_graph_nodes_by_id,
)


def _as_str(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _normalize_shape_node(node: dict[str, Any]) -> None:
    sc = node.get("shape_code", "")
    if sc is not None and not isinstance(sc, str):
        raise ValueError("shape.shape_code must be a string")
    node["shape_code"] = str(sc).strip() if isinstance(sc, str) else ""
    node.setdefault("role", "intermediate")
    node.setdefault("quantity", 1)


def _normalize_operation_node(node: dict[str, Any], index: int) -> None:
    opv = _as_str(node.get("operation"), label="operation.operation")
    try:
        op_enum = OperationType(opv)
    except ValueError as exc:
        raise ValueError(f"unknown operation type: {opv}") from exc
    if op_enum == OperationType.PAINTER:
        pc = node.get("paint_color")
        if pc is not None:
            if not isinstance(pc, str) or len(pc.strip()) != 1:
                raise ValueError(
                    f"nodes[{index}]: painter paint_color must be "
                    "a single character when set (legacy fallback)",
                )
            node["paint_color"] = pc.strip()
        return
    if op_enum == OperationType.CRYSTAL_GENERATOR:
        cc = node.get("crystal_color")
        if cc is None:
            return
        if not isinstance(cc, str) or len(cc.strip()) != 1:
            raise ValueError(
                f"nodes[{index}]: crystal_generator crystal_color must be "
                "a single character when set (or omit to infer from second input)",
            )
        node["crystal_color"] = cc.strip()


def _validate_graph_node(node: object, index: int, seen_ids: set[str]) -> None:
    if not isinstance(node, dict):
        raise ValueError(f"nodes[{index}] must be an object")
    nid = _as_str(node.get("id"), label="node.id")
    if nid in seen_ids:
        raise ValueError(f"duplicate node id: {nid}")
    seen_ids.add(nid)
    kind = _as_str(node.get("kind"), label="node.kind")
    if kind not in {"shape", "operation"}:
        raise ValueError(f"invalid node kind: {kind}")
    if kind == "shape":
        _normalize_shape_node(node)
    else:
        _normalize_operation_node(node, index)
    node.setdefault("x", 0.0)
    node.setdefault("y", 0.0)


def _validate_graph_edge_row(edge: object, index: int) -> None:
    if not isinstance(edge, dict):
        raise ValueError(f"edges[{index}] must be an object")
    _as_str(edge.get("from"), label="edge.from")
    _as_str(edge.get("to"), label="edge.to")
    ek = _as_str(edge.get("kind"), label="edge.kind")
    if ek not in {"input", "output", "delivery"}:
        raise ValueError(f"invalid edge kind: {ek}")
    if edge.get("slot") is not None and not isinstance(edge["slot"], str):
        raise ValueError("edge.slot must be a string or null")


def _assert_edges_reference_known_nodes(edges: list[dict[str, Any]], seen_ids: set[str]) -> None:
    for edge in edges:
        if edge["from"] not in seen_ids or edge["to"] not in seen_ids:
            raise ValueError(f"edge references unknown node: {edge}")


def validate_graph_document(raw: object) -> dict[str, Any]:
    """graph_document JSON 검증. 통과 시 정규화된 dict 반환."""
    if raw is None:
        raise ValueError("graph_document is required")
    if not isinstance(raw, dict):
        raise ValueError("graph_document must be an object")
    doc = copy.deepcopy(raw)
    ver = doc.get("schema_version", RECIPE_GRAPH_SCHEMA_VERSION)
    if int(ver) != RECIPE_GRAPH_SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {ver}")
    nodes = doc.get("nodes")
    edges = doc.get("edges")
    if not isinstance(nodes, list):
        raise ValueError("nodes must be a list")
    if not isinstance(edges, list):
        raise ValueError("edges must be a list")
    seen_ids: set[str] = set()
    for i, node in enumerate(nodes):
        _validate_graph_node(node, i, seen_ids)
    for i, edge in enumerate(edges):
        _validate_graph_edge_row(edge, i)
    _assert_edges_reference_known_nodes(edges, seen_ids)
    doc["schema_version"] = RECIPE_GRAPH_SCHEMA_VERSION
    doc["nodes"] = nodes
    doc["edges"] = edges
    assert_recipe_graph_edge_topology(doc)
    assert_delivery_targets_unique(edges)
    return doc


def default_empty_graph_document() -> dict[str, Any]:
    """검증을 통과한 빈 레시피 그래프(JSON). 신규 ``MacroRecipe`` 기본값으로 쓴다."""
    return validate_graph_document(
        {"schema_version": RECIPE_GRAPH_SCHEMA_VERSION, "nodes": [], "edges": []},
    )


def _apply_delivery_edges(
    edges: list[dict[str, Any]],
    *,
    node_by_id: dict[str, dict[str, Any]],
) -> None:
    """연산 재계산 후 intermediate의 ``shape_code``를 delivery 링크로 target에 복사한다."""
    for e in edges:
        if e.get("kind") != "delivery":
            continue
        src = node_by_id.get(str(e["from"]))
        tgt = node_by_id.get(str(e["to"]))
        if not src or not tgt:
            continue
        code = str(src.get("shape_code", "")).strip()
        if code:
            tgt["shape_code"] = code


def _shape_op_edge_action(
    e: dict[str, Any],
    node_kind: dict[str, Any],
) -> tuple[str, str, str] | None:
    """Return (role, shape_id, op_id) with role ``produce`` or ``consume``, else None."""
    fr, to = e["from"], e["to"]
    ek = e["kind"]
    if ek == "output" and node_kind.get(fr) == "operation" and node_kind.get(to) == "shape":
        return ("produce", to, fr)
    if ek == "input" and node_kind.get(fr) == "shape" and node_kind.get(to) == "operation":
        return ("consume", fr, to)
    return None


def _operation_dep_pairs_from_shape_links(
    shape_producers: dict[str, list[str]],
    shape_consumers: dict[str, list[str]],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for shape_id, consumers in shape_consumers.items():
        producers = shape_producers.get(shape_id, [])
        for prod in producers:
            for cons in consumers:
                if prod != cons:
                    pairs.append((prod, cons))
    return pairs


def _operation_dependency_edges(
    edges: list[dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
) -> list[tuple[str, str]]:
    """Return list of (producer_op_id, consumer_op_id) where consumer runs after producer."""
    node_kind = {nid: n.get("kind") for nid, n in node_by_id.items()}
    shape_producers: dict[str, list[str]] = defaultdict(list)
    shape_consumers: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        action = _shape_op_edge_action(e, node_kind)
        if action is None:
            continue
        role, shape_id, op_id = action
        if role == "produce":
            shape_producers[shape_id].append(op_id)
        else:
            shape_consumers[shape_id].append(op_id)
    return _operation_dep_pairs_from_shape_links(shape_producers, shape_consumers)


def _edge_adjacency(
    edges: list[dict[str, Any]],
) -> tuple[defaultdict[str, list[dict[str, Any]]], defaultdict[str, list[dict[str, Any]]]]:
    """input: to → edges, output: from → edges (참조는 원본 edge dict와 동일)."""
    input_edges_by_to: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    output_edges_by_from: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in edges:
        ek = e.get("kind")
        if ek == "input":
            input_edges_by_to[str(e["to"])].append(e)
        elif ek == "output":
            output_edges_by_from[str(e["from"])].append(e)
    return input_edges_by_to, output_edges_by_from


def _topological_operation_order(op_ids: list[str], dep_pairs: list[tuple[str, str]]) -> list[str]:
    if not op_ids:
        return []
    succ: dict[str, set[str]] = defaultdict(set)
    indeg: dict[str, int] = dict.fromkeys(op_ids, 0)
    op_set = set(op_ids)
    for a, b in dep_pairs:
        if a in op_set and b in op_set and b not in succ[a]:
            succ[a].add(b)
            indeg[b] += 1
    q = deque([oid for oid in op_ids if indeg[oid] == 0])
    out: list[str] = []
    while q:
        u = q.popleft()
        out.append(u)
        for v in succ.get(u, ()):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    if len(out) != len(op_set):
        raise ValueError("operation graph contains a cycle or disconnected ops")
    return out


def _output_edge_sort_key(e: dict[str, Any]) -> tuple[bool, str, str]:
    return (
        e.get("slot") is None,
        str(e.get("slot") or ""),
        str(e.get("id") or ""),
    )


def _sorted_input_codes_for_operation(
    node_by_id: dict[str, dict[str, Any]],
    input_edges: list[dict[str, Any]],
) -> tuple[str, ...]:
    rows: list[tuple[bool, str, str, str]] = []
    for e in input_edges:
        sid = e["from"]
        shape = node_by_id.get(sid)
        if not shape or shape.get("kind") != "shape":
            continue
        code = str(shape.get("shape_code", "")).strip()
        slot = e.get("slot")
        slot_key = slot if isinstance(slot, str) and slot.strip() else ""
        has_slot = bool(slot_key)
        rows.append((not has_slot, slot_key, sid, code))
    rows.sort(key=lambda t: (t[0], t[1], t[2]))
    return tuple(t[3] for t in rows)


def _sorted_output_edges_for_operation(
    op_id: str,
    output_edges_by_from: defaultdict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    out_edges = output_edges_by_from[op_id]
    out_edges.sort(key=_output_edge_sort_key)
    return out_edges


def _new_shape_id(existing: set[str]) -> str:
    for _ in range(64):
        nid = f"shape_{uuid.uuid4().hex[:10]}"
        if nid not in existing:
            return nid
    raise RuntimeError("could not allocate shape node id")


_TWO_INPUT_OPERATION_TYPES = frozenset(
    {
        OperationType.SWAPPER,
        OperationType.STACKER,
        OperationType.COLOR_MIXER,
        OperationType.CRYSTAL_GENERATOR,
    },
)


def _required_input_count_for_recompute(
    op_type: OperationType,
    op_node: dict[str, Any],
) -> int:
    if op_type == OperationType.PAINTER:
        pc = str(op_node.get("paint_color", "")).strip()
        return 1 if pc else 2
    if op_type in _TWO_INPUT_OPERATION_TYPES:
        return 2
    return 1


def _apply_recomputed_operation(
    op_id: str,
    op_type: OperationType,
    input_codes: list[str],
    op_node: dict[str, Any],
    *,
    shape_parse_cache: dict[str, Shape],
) -> tuple[bool, tuple[str, ...], str]:
    """(성공 여부, 출력 shape_code 튜플, 경고 메시지). 실패 시 튜플은 빈 값."""
    need = _required_input_count_for_recompute(op_type, op_node)
    if len(input_codes) != need:
        return (
            False,
            (),
            f"skip op {op_id}: expected {need} inputs, got {len(input_codes)}",
        )
    try:
        if op_type == OperationType.PAINTER:
            pc = str(op_node.get("paint_color", "")).strip() or None
            outputs = apply_operation(
                op_type,
                tuple(input_codes),
                paint_color=pc,
                shape_parse_cache=shape_parse_cache,
            )
        elif op_type == OperationType.CRYSTAL_GENERATOR:
            cc = str(op_node.get("crystal_color", "")).strip()
            outputs = apply_operation(
                op_type,
                tuple(input_codes),
                crystal_color=cc or None,
                shape_parse_cache=shape_parse_cache,
            )
        else:
            outputs = apply_operation(
                op_type,
                tuple(input_codes),
                shape_parse_cache=shape_parse_cache,
            )
    except (ValueError, TypeError, KeyError) as exc:
        return False, (), f"op {op_id} failed: {exc}"
    return True, outputs, ""


def _assign_operation_outputs(
    op_id: str,
    op_node: dict[str, Any],
    outputs: tuple[str, ...],
    out_edges: list[dict[str, Any]],
    *,
    node_by_id: dict[str, dict[str, Any]],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    output_edges_by_from: defaultdict[str, list[dict[str, Any]]],
    existing_ids: set[str],
    warnings: list[str],
) -> None:
    ox = float(op_node.get("x", 0))
    oy = float(op_node.get("y", 0))
    grid_cols = max(1, int(RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS))

    for i, out_code in enumerate(outputs):
        if i < len(out_edges):
            e = out_edges[i]
            target = node_by_id.get(e["to"])
            if target and target.get("kind") == "shape":
                target["shape_code"] = out_code
            continue
        nid = _new_shape_id(existing_ids)
        existing_ids.add(nid)
        col = i % grid_cols
        row = i // grid_cols
        nx = (
            ox
            + RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET
            + col * float(RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING)
        )
        ny = oy + row * float(RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING)
        new_shape: dict[str, Any] = {
            "id": nid,
            "kind": "shape",
            "role": "intermediate",
            "shape_code": out_code,
            "quantity": 1,
            "x": nx,
            "y": ny,
        }
        nodes.append(new_shape)
        node_by_id[nid] = new_shape
        new_edge: dict[str, Any] = {
            "from": op_id,
            "to": nid,
            "kind": "output",
            "slot": str(i),
        }
        edges.append(new_edge)
        output_edges_by_from[op_id].append(new_edge)
        warnings.append(f"auto-created shape node {nid} for output {i} of {op_id}")

    if len(out_edges) > len(outputs):
        warnings.append(
            f"op {op_id}: {len(out_edges)} output edges but only {len(outputs)} outputs",
        )


def recompute_validated_graph_document(work: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    ``validate_graph_document`` 를 통과한 문서에 대해 재계산만 수행한다(추가 deepcopy 없음).

    ``work`` 는 호출부가 소유하며 이 함수가 노드·엣지를 갱신한다.
    """
    warnings: list[str] = []
    nodes: list[dict[str, Any]] = work["nodes"]
    edges: list[dict[str, Any]] = work["edges"]
    node_by_id = index_recipe_graph_nodes_by_id(nodes)
    op_ids = [nid for nid, n in node_by_id.items() if n.get("kind") == "operation"]
    dep_pairs = _operation_dependency_edges(edges, node_by_id)
    try:
        topo = _topological_operation_order(op_ids, dep_pairs)
    except ValueError as exc:
        warnings.append(str(exc))
        return work, warnings

    existing_ids = set(node_by_id)
    input_edges_by_to, output_edges_by_from = _edge_adjacency(edges)
    shape_parse_cache: dict[str, Shape] = {}

    for op_id in topo:
        op_node = node_by_id.get(op_id)
        if not op_node or op_node.get("kind") != "operation":
            continue
        op_key = str(op_node.get("operation", "")).strip()
        if op_key not in RECIPE_GRAPH_ENGINE_OPERATIONS:
            warnings.append(f"skip unsupported operation: {op_key} ({op_id})")
            continue
        op_type = OperationType(op_key)
        input_codes = list(
            _sorted_input_codes_for_operation(node_by_id, input_edges_by_to[op_id]),
        )
        if not input_codes:
            warnings.append(f"skip op with no inputs: {op_id}")
            continue
        if any(not code for code in input_codes):
            warnings.append(f"skip op with empty shape_code on input: {op_id}")
            continue
        ok, outputs, msg = _apply_recomputed_operation(
            op_id,
            op_type,
            input_codes,
            op_node,
            shape_parse_cache=shape_parse_cache,
        )
        if not ok:
            warnings.append(msg)
            continue

        out_edges = _sorted_output_edges_for_operation(op_id, output_edges_by_from)
        _assign_operation_outputs(
            op_id,
            op_node,
            outputs,
            out_edges,
            node_by_id=node_by_id,
            nodes=nodes,
            edges=edges,
            output_edges_by_from=output_edges_by_from,
            existing_ids=existing_ids,
            warnings=warnings,
        )

    _apply_delivery_edges(edges, node_by_id=node_by_id)

    work["nodes"] = nodes
    work["edges"] = edges
    return work, warnings


def recompute_graph_document(doc: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    연결이 갖춰진 operation에 대해 apply_operation으로 하류 shape_code를 갱신한다.

    Returns (updated_document, warnings).
    """
    work = validate_graph_document(doc)
    return recompute_validated_graph_document(work)


def _validated_graph_document_for_pattern_macro(raw: object) -> dict[str, Any] | None:
    """``try_pattern_macro_step_rows_from_graph_document`` 선행 검증. 실패 시 ``None``."""
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return None
    nodes_raw = raw.get("nodes")
    if not isinstance(nodes_raw, list) or not nodes_raw:
        return None
    try:
        return validate_graph_document(raw)
    except ValueError:
        return None


def _output_slots_strings_for_edges(
    out_edges: list[dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    """output 엣리스트를 Pattern Macro 스텝의 ``output_slots`` 문자열 목록으로 바꾼다."""
    output_slots_list: list[str] = []
    for e in out_edges:
        tid = str(e.get("to") or "")
        shape = node_by_id.get(tid)
        if shape and shape.get("kind") == "shape":
            oc = str(shape.get("shape_code", "")).strip()
            output_slots_list.append(oc)
        else:
            output_slots_list.append(tid or "?")
    return output_slots_list


def try_pattern_macro_step_rows_from_graph_document(raw: object) -> list[dict[str, Any]] | None:
    """
    Pattern Lab·스태프 카탈로그용: ``graph_document``에서 operation 위상순 스텝 요약을 만든다.

    - 검증 실패·DAG 사이클·operation 노드 없음 → ``None`` (DB ``MacroRecipeStep`` 사용).
    - 성공 시 ``step_index``는 1부터 위상순으로 채운다.
    """
    work = _validated_graph_document_for_pattern_macro(raw)
    if work is None:
        return None
    nodes: list[dict[str, Any]] = work["nodes"]
    edges: list[dict[str, Any]] = work["edges"]
    node_by_id = index_recipe_graph_nodes_by_id(nodes)
    op_ids = [nid for nid, n in node_by_id.items() if n.get("kind") == "operation"]
    if not op_ids:
        return None
    dep_pairs = _operation_dependency_edges(edges, node_by_id)
    try:
        topo = _topological_operation_order(op_ids, dep_pairs)
    except ValueError:
        return None
    input_edges_by_to, output_edges_by_from = _edge_adjacency(edges)
    out: list[dict[str, Any]] = []
    step_index = 0
    for op_id in topo:
        op_node = node_by_id.get(op_id)
        if not op_node or op_node.get("kind") != "operation":
            continue
        op_key = str(op_node.get("operation") or "").strip()
        if not op_key:
            continue
        step_index += 1
        input_codes = _sorted_input_codes_for_operation(node_by_id, input_edges_by_to[op_id])
        out_edges = _sorted_output_edges_for_operation(op_id, output_edges_by_from)
        output_slots_list = _output_slots_strings_for_edges(out_edges, node_by_id)
        out.append(
            {
                "step_index": step_index,
                "operation": op_key,
                "input_slots": list(input_codes),
                "output_slots": output_slots_list,
                "note": f"graph:{op_id}",
            },
        )
    return out if out else None


__all__ = [
    "default_empty_graph_document",
    "recompute_graph_document",
    "recompute_validated_graph_document",
    "try_pattern_macro_step_rows_from_graph_document",
    "validate_graph_document",
]
