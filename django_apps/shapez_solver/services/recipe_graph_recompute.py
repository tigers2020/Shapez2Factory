"""Recipe graph document: validate, topo order, and engine-backed recompute."""

from __future__ import annotations

import copy
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass

from config.log_timing import log_timing
from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.domain.shape_catalog import FLUID_SOURCE_PRIMARY_COLORS
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.fluid_semantics import pure_fluid_color
from django_apps.shapez_solver.services.operation_semantics import apply_operation, parse_shape
from django_apps.shapez_solver.services.recipe_graph_constants import (
    RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING,
    RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS,
    RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING,
    RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET,
    RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_FLUID,
    RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_MATERIAL,
    RECIPE_GRAPH_ENGINE_OPERATIONS,
    RECIPE_GRAPH_SCHEMA_VERSION,
)
from django_apps.shapez_solver.services.recipe_graph_input_carrier import (
    assert_input_output_carriers_for_document,
    operation_output_lane_carrier,
    shape_node_is_fluid,
    sorted_shape_input_edges_to_operation,
)
from django_apps.shapez_solver.services.recipe_graph_source_carrier import (
    assert_fluid_carrier_shape_for_role,
)
from django_apps.shapez_solver.services.recipe_graph_topology import (
    assert_delivery_targets_unique,
    assert_recipe_graph_edge_topology,
    index_recipe_graph_nodes_by_id,
)

logger = logging.getLogger(__name__)


def _as_str(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _normalize_shape_node_shape_code(node: dict[str, object]) -> None:
    sc = node.get("shape_code", "")
    if sc is not None and not isinstance(sc, str):
        raise ValueError("shape.shape_code must be a string")
    node["shape_code"] = str(sc).strip() if isinstance(sc, str) else ""


def _normalize_shape_node_source_carrier(
    node: dict[str, object],
    index: int,
    role: str,
) -> None:
    raw_carrier = node.get("source_carrier")
    if raw_carrier is None or (isinstance(raw_carrier, str) and raw_carrier.strip() == ""):
        node.pop("source_carrier", None)
        return
    if not isinstance(raw_carrier, str):
        raise ValueError(f"nodes[{index}]: shape.source_carrier must be a string or omitted")
    c = raw_carrier.strip()
    if c not in ("material", "fluid"):
        raise ValueError(f"nodes[{index}]: invalid shape.source_carrier: {raw_carrier!r}")
    if c == "material":
        node.pop("source_carrier", None)
        return
    node["source_carrier"] = "fluid"
    if role not in ("source", "intermediate"):
        raise ValueError(
            f"nodes[{index}]: source_carrier=fluid requires role=source or intermediate, "
            f"got role={role!r}",
        )


def _normalize_shape_node(node: dict[str, object], *, index: int) -> None:
    _normalize_shape_node_shape_code(node)
    node.setdefault("role", "intermediate")
    role = str(node.get("role", "intermediate")).strip()
    node["role"] = role
    if role == "target":
        node.pop("source_carrier", None)
    _normalize_shape_node_source_carrier(node, index, role)
    if "quantity" not in node:
        if node.get("source_carrier") == "fluid":
            node["quantity"] = RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_FLUID
        elif role == "source":
            node["quantity"] = RECIPE_GRAPH_DEFAULT_SOURCE_QUANTITY_MATERIAL
        else:
            node["quantity"] = 1


def _normalize_painter_paint_color(node: dict[str, object], index: int) -> None:
    pc = node.get("paint_color")
    if pc is None:
        return
    if not isinstance(pc, str) or len(pc.strip()) != 1:
        raise ValueError(
            f"nodes[{index}]: painter paint_color must be "
            "a single character when set (legacy fallback)",
        )
    ink = pc.strip()
    if ink not in FLUID_SOURCE_PRIMARY_COLORS:
        raise ValueError(
            f"nodes[{index}]: painter paint_color must be one of "
            f"{sorted(FLUID_SOURCE_PRIMARY_COLORS)}, got {ink!r}",
        )
    node["paint_color"] = ink


def _normalize_crystal_generator_crystal_color(node: dict[str, object], index: int) -> None:
    cc = node.get("crystal_color")
    if cc is None:
        return
    if not isinstance(cc, str) or len(cc.strip()) != 1:
        raise ValueError(
            f"nodes[{index}]: crystal_generator crystal_color must be "
            "a single character when set (or omit to infer from second input)",
        )
    node["crystal_color"] = cc.strip()


def _normalize_operation_node(node: dict[str, object], index: int) -> None:
    opv = _as_str(node.get("operation"), label="operation.operation")
    try:
        op_enum = OperationType(opv)
    except ValueError as exc:
        raise ValueError(f"unknown operation type: {opv}") from exc
    if op_enum == OperationType.PAINTER:
        _normalize_painter_paint_color(node, index)
        return
    if op_enum == OperationType.CRYSTAL_GENERATOR:
        _normalize_crystal_generator_crystal_color(node, index)


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
        _normalize_shape_node(node, index=index)
        if node.get("source_carrier") == "fluid":
            assert_fluid_carrier_shape_for_role(
                str(node.get("role", "intermediate")),
                str(node.get("shape_code", "")),
                index=index,
                node_id=nid,
            )
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


def _assert_edges_reference_known_nodes(edges: list[dict[str, object]], seen_ids: set[str]) -> None:
    for edge in edges:
        if edge["from"] not in seen_ids or edge["to"] not in seen_ids:
            raise ValueError(f"edge references unknown node: {edge}")


def validate_graph_document(raw: object) -> dict[str, object]:
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
    assert_input_output_carriers_for_document(doc)
    return doc


def default_empty_graph_document() -> dict[str, object]:
    """검증을 통과한 빈 레시피 그래프(JSON)."""
    return validate_graph_document(
        {"schema_version": RECIPE_GRAPH_SCHEMA_VERSION, "nodes": [], "edges": []},
    )


def _apply_delivery_edges(
    edges: list[dict[str, object]],
    *,
    node_by_id: dict[str, dict[str, object]],
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
    e: dict[str, object],
    node_kind: dict[str, object],
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
    edges: list[dict[str, object]],
    node_by_id: dict[str, dict[str, object]],
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
    edges: list[dict[str, object]],
) -> tuple[defaultdict[str, list[dict[str, object]]], defaultdict[str, list[dict[str, object]]]]:
    """input: to → edges, output: from → edges (참조는 원본 edge dict와 동일)."""
    input_edges_by_to: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    output_edges_by_from: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
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


def _output_edge_sort_key(e: dict[str, object]) -> tuple[bool, str, str]:
    return (
        e.get("slot") is None,
        str(e.get("slot") or ""),
        str(e.get("id") or ""),
    )


def _shape_quantity_int(shape_node: dict[str, object]) -> int:
    raw_q = shape_node.get("quantity", 1)
    if isinstance(raw_q, bool) or not isinstance(raw_q, int):
        return 1
    q: int = raw_q
    return max(1, q)


def _merge_input_quantity_sum(
    node_by_id: dict[str, dict[str, object]],
    input_edges: list[dict[str, object]],
    *,
    need: int,
) -> int:
    ordered = sorted_shape_input_edges_to_operation(input_edges, node_by_id)
    total = 0
    for edge in ordered[:need]:
        sid = str(edge.get("from", ""))
        src = node_by_id.get(sid)
        if not src or src.get("kind") != "shape":
            continue
        total += _shape_quantity_int(src)
    return max(1, total)


def _cutter_output_quantities(
    node_by_id: dict[str, dict[str, object]],
    input_edges: list[dict[str, object]],
) -> tuple[int, int]:
    """세로 컷: 조각 수를 반으로 나눈다(풀 4 → 2+2). ``quantity``<2 는 레거시로 (1,1)."""

    ordered = sorted_shape_input_edges_to_operation(input_edges, node_by_id)
    if not ordered:
        return (1, 1)
    sid = str(ordered[0].get("from", ""))
    src = node_by_id.get(sid)
    if not src or src.get("kind") != "shape":
        return (1, 1)
    q_in = _shape_quantity_int(src)
    if q_in < 2:
        return (1, 1)
    q_left = q_in // 2
    q_right = q_in - q_left
    return (q_left, q_right)


def _sorted_input_codes_for_operation(
    node_by_id: dict[str, dict[str, object]],
    input_edges: list[dict[str, object]],
) -> tuple[str, ...]:
    ordered = sorted_shape_input_edges_to_operation(input_edges, node_by_id)
    codes: list[str] = []
    for e in ordered:
        sid = str(e.get("from", ""))
        shape = node_by_id.get(sid)
        if not shape or shape.get("kind") != "shape":
            continue
        codes.append(str(shape.get("shape_code", "")).strip())
    return tuple(codes)


def _pattern_macro_input_slot_label(
    shape_node: dict[str, object],
    shape_code: str,
    *,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> str:
    """Pattern macro UI: fluid wire는 균일 잉크 한 글자만; 재료(shape)는 기존 shape_code."""

    if not shape_node_is_fluid(shape_node):
        return shape_code
    if not shape_code:
        return shape_code
    try:
        return pure_fluid_color(parse_shape(shape_code, cache=shape_parse_cache))
    except (ValueError, TypeError, KeyError):
        return shape_code


def _sorted_pattern_macro_input_slots(
    node_by_id: dict[str, dict[str, object]],
    input_edges: list[dict[str, object]],
    *,
    shape_parse_cache: dict[str, Shape] | None = None,
) -> list[str]:
    ordered = sorted_shape_input_edges_to_operation(input_edges, node_by_id)
    slots: list[str] = []
    for e in ordered:
        sid = str(e.get("from", ""))
        shape = node_by_id.get(sid)
        if not shape or shape.get("kind") != "shape":
            continue
        code = str(shape.get("shape_code", "")).strip()
        slots.append(
            _pattern_macro_input_slot_label(shape, code, shape_parse_cache=shape_parse_cache),
        )
    return slots


def _sorted_output_edges_for_operation(
    op_id: str,
    output_edges_by_from: defaultdict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
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
        OperationType.MERGE,
        OperationType.COLOR_MIXER,
    },
)


def _required_input_count_for_recompute(
    op_type: OperationType,
    op_node: dict[str, object],
) -> int:
    if op_type == OperationType.PAINTER:
        pc = str(op_node.get("paint_color", "")).strip()
        return 1 if pc else 2
    if op_type == OperationType.CRYSTAL_GENERATOR:
        cc = str(op_node.get("crystal_color", "")).strip()
        return 1 if cc else 2
    if op_type in _TWO_INPUT_OPERATION_TYPES:
        return 2
    return 1


def _apply_recomputed_operation(
    op_id: str,
    op_type: OperationType,
    input_codes: list[str],
    op_node: dict[str, object],
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


def _apply_operation_output_lane_to_shape_node(
    shape_node: dict[str, object],
    op_type: OperationType,
    lane_index: int,
) -> None:
    if operation_output_lane_carrier(op_type, lane_index) == "fluid":
        shape_node["source_carrier"] = "fluid"
    else:
        shape_node.pop("source_carrier", None)


@dataclass
class _RecomputeGraphMutation:
    node_by_id: dict[str, dict[str, object]]
    nodes: list[dict[str, object]]
    edges: list[dict[str, object]]
    output_edges_by_from: defaultdict[str, list[dict[str, object]]]
    existing_ids: set[str]
    warnings: list[str]


def _fill_linked_shape_from_operation_output(
    edge: dict[str, object],
    out_code: str,
    op_type: OperationType,
    lane_index: int,
    *,
    node_by_id: dict[str, dict[str, object]],
    output_quantities: tuple[int, ...] | None,
) -> None:
    target = node_by_id.get(edge["to"])
    if not target or target.get("kind") != "shape":
        return
    target["shape_code"] = out_code
    if output_quantities is not None and lane_index < len(output_quantities):
        target["quantity"] = max(1, int(output_quantities[lane_index]))
    _apply_operation_output_lane_to_shape_node(target, op_type, lane_index)


def _append_auto_created_operation_output_shape(
    op_id: str,
    op_type: OperationType,
    lane_index: int,
    out_code: str,
    ox: float,
    oy: float,
    grid_cols: int,
    mutation: _RecomputeGraphMutation,
    output_quantities: tuple[int, ...] | None,
) -> None:
    nid = _new_shape_id(mutation.existing_ids)
    mutation.existing_ids.add(nid)
    col = lane_index % grid_cols
    row = lane_index // grid_cols
    nx = ox + RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET + col * float(RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING)
    ny = oy + row * float(RECIPE_GRAPH_AUTO_OUTPUT_ROW_SPACING)
    q_new = 1
    if output_quantities is not None and lane_index < len(output_quantities):
        q_new = max(1, int(output_quantities[lane_index]))
    new_shape: dict[str, object] = {
        "id": nid,
        "kind": "shape",
        "role": "intermediate",
        "shape_code": out_code,
        "quantity": q_new,
        "x": nx,
        "y": ny,
    }
    _apply_operation_output_lane_to_shape_node(new_shape, op_type, lane_index)
    mutation.nodes.append(new_shape)
    mutation.node_by_id[nid] = new_shape
    new_edge: dict[str, object] = {
        "from": op_id,
        "to": nid,
        "kind": "output",
        "slot": str(lane_index),
    }
    mutation.edges.append(new_edge)
    mutation.output_edges_by_from[op_id].append(new_edge)
    mutation.warnings.append(f"auto-created shape node {nid} for output {lane_index} of {op_id}")


def _assign_operation_outputs(
    op_id: str,
    op_type: OperationType,
    op_node: dict[str, object],
    outputs: tuple[str, ...],
    out_edges: list[dict[str, object]],
    *,
    node_by_id: dict[str, dict[str, object]],
    nodes: list[dict[str, object]],
    edges: list[dict[str, object]],
    output_edges_by_from: defaultdict[str, list[dict[str, object]]],
    existing_ids: set[str],
    warnings: list[str],
    output_quantities: tuple[int, ...] | None = None,
) -> None:
    ox = float(op_node.get("x", 0))
    oy = float(op_node.get("y", 0))
    grid_cols = max(1, int(RECIPE_GRAPH_AUTO_OUTPUT_GRID_COLUMNS))
    mutation = _RecomputeGraphMutation(
        node_by_id=node_by_id,
        nodes=nodes,
        edges=edges,
        output_edges_by_from=output_edges_by_from,
        existing_ids=existing_ids,
        warnings=warnings,
    )

    for i, out_code in enumerate(outputs):
        if i < len(out_edges):
            _fill_linked_shape_from_operation_output(
                out_edges[i],
                out_code,
                op_type,
                i,
                node_by_id=node_by_id,
                output_quantities=output_quantities,
            )
            continue
        _append_auto_created_operation_output_shape(
            op_id,
            op_type,
            i,
            out_code,
            ox,
            oy,
            grid_cols,
            mutation,
            output_quantities,
        )

    if len(out_edges) > len(outputs):
        warnings.append(
            f"op {op_id}: {len(out_edges)} output edges but only {len(outputs)} outputs",
        )


def _output_quantities_for_recomputed_op(
    op_type: OperationType,
    op_node: dict[str, object],
    *,
    node_by_id: dict[str, dict[str, object]],
    input_edges: list[dict[str, object]],
) -> tuple[int, ...] | None:
    """MERGE/STACKER/CUTTER 등 출력 레인별 수량이 필요할 때만 튜플을 반환한다."""
    need_in = _required_input_count_for_recompute(op_type, op_node)
    if op_type in (OperationType.MERGE, OperationType.STACKER):
        return (_merge_input_quantity_sum(node_by_id, input_edges, need=need_in),)
    if op_type == OperationType.CUTTER:
        return _cutter_output_quantities(node_by_id, input_edges)
    return None


def _recompute_one_operation_in_topo(
    op_id: str,
    *,
    node_by_id: dict[str, dict[str, object]],
    nodes: list[dict[str, object]],
    edges: list[dict[str, object]],
    input_edges_by_to: defaultdict[str, list[dict[str, object]]],
    output_edges_by_from: defaultdict[str, list[dict[str, object]]],
    existing_ids: set[str],
    warnings: list[str],
    shape_parse_cache: dict[str, Shape],
) -> None:
    op_node = node_by_id.get(op_id)
    if not op_node or op_node.get("kind") != "operation":
        return
    op_key = str(op_node.get("operation", "")).strip()
    if op_key not in RECIPE_GRAPH_ENGINE_OPERATIONS:
        warnings.append(f"skip unsupported operation: {op_key} ({op_id})")
        return
    op_type = OperationType(op_key)
    input_codes = list(
        _sorted_input_codes_for_operation(node_by_id, input_edges_by_to[op_id]),
    )
    if not input_codes:
        warnings.append(f"skip op with no inputs: {op_id}")
        return
    if any(not code for code in input_codes):
        warnings.append(f"skip op with empty shape_code on input: {op_id}")
        return
    ok, outputs, msg = _apply_recomputed_operation(
        op_id,
        op_type,
        input_codes,
        op_node,
        shape_parse_cache=shape_parse_cache,
    )
    if not ok:
        if op_type == OperationType.SWAPPER:
            logger.warning(
                "recipe_graph_swapper_failed",
                extra={"op_id": op_id, "reason": msg, "inputs": input_codes},
            )
        warnings.append(msg)
        return

    if op_type == OperationType.SWAPPER:
        logger.info(
            "recipe_graph_swapper_ok",
            extra={"op_id": op_id, "inputs": input_codes, "outputs": outputs},
        )
    out_edges = _sorted_output_edges_for_operation(op_id, output_edges_by_from)
    output_quantities = _output_quantities_for_recomputed_op(
        op_type,
        op_node,
        node_by_id=node_by_id,
        input_edges=input_edges_by_to[op_id],
    )
    _assign_operation_outputs(
        op_id,
        op_type,
        op_node,
        outputs,
        out_edges,
        node_by_id=node_by_id,
        nodes=nodes,
        edges=edges,
        output_edges_by_from=output_edges_by_from,
        existing_ids=existing_ids,
        warnings=warnings,
        output_quantities=output_quantities,
    )


def recompute_validated_graph_document(
    work: dict[str, object],
) -> tuple[dict[str, object], list[str]]:
    """
    ``validate_graph_document`` 를 통과한 문서에 대해 재계산만 수행한다(추가 deepcopy 없음).

    ``work`` 는 호출부가 소유하며 이 함수가 노드·엣지를 갱신한다.
    """
    warnings: list[str] = []
    nodes: list[dict[str, object]] = work["nodes"]
    edges: list[dict[str, object]] = work["edges"]
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
        _recompute_one_operation_in_topo(
            op_id,
            node_by_id=node_by_id,
            nodes=nodes,
            edges=edges,
            input_edges_by_to=input_edges_by_to,
            output_edges_by_from=output_edges_by_from,
            existing_ids=existing_ids,
            warnings=warnings,
            shape_parse_cache=shape_parse_cache,
        )

    _apply_delivery_edges(edges, node_by_id=node_by_id)

    work["nodes"] = nodes
    work["edges"] = edges
    return work, warnings


def recompute_graph_document(doc: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    """
    연결이 갖춰진 operation에 대해 apply_operation으로 하류 shape_code를 갱신한다.

    Returns (updated_document, warnings).
    """
    work = validate_graph_document(doc)
    with log_timing(
        logger,
        "recipe_graph_recompute",
        node_count=len(work.get("nodes", [])),
    ):
        return recompute_validated_graph_document(work)


def _validated_graph_document_for_pattern_macro(raw: object) -> dict[str, object] | None:
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
    out_edges: list[dict[str, object]],
    node_by_id: dict[str, dict[str, object]],
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


def try_pattern_macro_step_rows_from_graph_document(raw: object) -> list[dict[str, object]] | None:
    """
    Pattern Lab·스태프 카탈로그용: ``graph_document``에서 operation 위상순 스텝 요약을 만든다.

    - 검증 실패·DAG 사이클·operation 노드 없음 → ``None``.
    - 성공 시 ``step_index``는 1부터 위상순으로 채운다.
    - ``input_slots``: ``source_carrier=fluid`` 입력은 균일 잉크 한 글자(예: ``r``)만 넣는다.
      재료(shape) 입력은 ``shape_code`` 그대로 (유체 전층 코드와 도형 코드 혼동 방지).
    """
    work = _validated_graph_document_for_pattern_macro(raw)
    if work is None:
        return None
    nodes: list[dict[str, object]] = work["nodes"]
    edges: list[dict[str, object]] = work["edges"]
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
    shape_parse_cache: dict[str, Shape] = {}
    out: list[dict[str, object]] = []
    step_index = 0
    for op_id in topo:
        op_node = node_by_id.get(op_id)
        if not op_node or op_node.get("kind") != "operation":
            continue
        op_key = str(op_node.get("operation") or "").strip()
        if not op_key:
            continue
        step_index += 1
        input_slots_display = _sorted_pattern_macro_input_slots(
            node_by_id,
            input_edges_by_to[op_id],
            shape_parse_cache=shape_parse_cache,
        )
        out_edges = _sorted_output_edges_for_operation(op_id, output_edges_by_from)
        output_slots_list = _output_slots_strings_for_edges(out_edges, node_by_id)
        out.append(
            {
                "step_index": step_index,
                "operation": op_key,
                "input_slots": input_slots_display,
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
