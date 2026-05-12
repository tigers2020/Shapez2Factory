"""Macro ``graph_document``에서 compile 경계(source/target) 패턴 행을 파생·동기화한다."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeCompiledBoundary
from django_apps.shapez_solver.services.pattern_classifier import pattern_signature
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document

MAX_COMPILED_END_BOUNDARIES = 4


def _edge_shape_link_sets(doc: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """input의 출발 shape id, output의 도착 shape id, delivery의 출발 shape id."""

    input_from: set[str] = set()
    output_to: set[str] = set()
    delivery_from: set[str] = set()
    for e in doc.get("edges") or []:
        if not isinstance(e, dict):
            continue
        k = str(e.get("kind", ""))
        fr = str(e.get("from", "")).strip()
        to = str(e.get("to", "")).strip()
        if k == "input" and fr:
            input_from.add(fr)
        elif k == "output" and to:
            output_to.add(to)
        elif k == "delivery" and fr:
            delivery_from.add(fr)
    return input_from, output_to, delivery_from


def _sink_intermediate_shape_ids(
    nodes: list[Any],
    *,
    input_from: set[str],
    output_to: set[str],
    delivery_from: set[str],
) -> set[str]:
    """연산 산출 intermediate이면서 다음 연산으로 안 가고 delivery 출발도 아닌 노드 id."""

    sinks: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("kind") != "shape":
            continue
        nid = str(node.get("id", "")).strip()
        if not nid:
            continue
        role = str(node.get("role", "intermediate")).strip()
        if role != "intermediate":
            continue
        if nid not in output_to:
            continue
        if nid in input_from:
            continue
        if nid in delivery_from:
            continue
        sinks.add(nid)
    return sinks


def _pattern_for_node(node: dict[str, Any]) -> str | None:
    code = str(node.get("shape_code", "")).strip()
    if not code:
        return None
    try:
        pattern = parse_shape_code_list(code)[0]
    except ShapeCodeParseError:
        return None
    if not pattern.layers:
        return None
    layer_str = "".join(cell.raw_token for cell in pattern.layers[0].cells)
    try:
        return pattern_signature(layer_str)
    except ValueError:
        return None


def _select_end_pairs(
    *,
    node_by_id: dict[str, dict[str, Any]],
    target_ids: list[str],
    sink_ids: set[str],
) -> list[tuple[str, str]]:
    """target 우선( id 오름차순 ), 이어서 싱크 intermediate( id 오름차순 ), 최대 4개."""

    end_targets: list[tuple[str, str]] = []
    for nid in sorted(target_ids):
        node = node_by_id.get(nid)
        if not node:
            continue
        sig = _pattern_for_node(node)
        if sig is None:
            continue
        end_targets.append((nid, sig))

    end_sinks: list[tuple[str, str]] = []
    for nid in sorted(sink_ids):
        node = node_by_id.get(nid)
        if not node:
            continue
        sig = _pattern_for_node(node)
        if sig is None:
            continue
        end_sinks.append((nid, sig))

    merged = end_targets + end_sinks
    return merged[:MAX_COMPILED_END_BOUNDARIES]


def compiled_boundary_specs_from_graph_document(
    graph_document: dict[str, Any],
) -> list[tuple[str, str, str]]:
    """검증된 graph_document에서 (graph_shape_id, pattern_signature, boundary DB 값) 튜플 목록."""

    try:
        doc = validate_graph_document(graph_document)
    except ValueError:
        return []

    nodes = doc.get("nodes") or []
    input_from, output_to, delivery_from = _edge_shape_link_sets(doc)
    sink_ids = _sink_intermediate_shape_ids(
        nodes,
        input_from=input_from,
        output_to=output_to,
        delivery_from=delivery_from,
    )

    node_by_id: dict[str, dict[str, Any]] = {}
    target_ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict) or node.get("kind") != "shape":
            continue
        nid = str(node.get("id", "")).strip()
        if not nid:
            continue
        node_by_id[nid] = node
        role = str(node.get("role", "intermediate")).strip()
        if role == "target":
            target_ids.append(nid)

    end_pairs = _select_end_pairs(
        node_by_id=node_by_id,
        target_ids=target_ids,
        sink_ids=sink_ids,
    )
    end_ids_chosen = {p[0] for p in end_pairs}

    rows: list[tuple[str, str, str]] = []
    boundary_end = str(MacroRecipeCompiledBoundary.Boundary.END)
    boundary_start = str(MacroRecipeCompiledBoundary.Boundary.START)

    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("kind") != "shape":
            continue
        nid = str(node.get("id", "")).strip()
        if not nid:
            continue
        role = str(node.get("role", "intermediate")).strip()
        if role == "source":
            sig = _pattern_for_node(node)
            if sig is None:
                continue
            rows.append((nid, sig, boundary_start))
            continue
        if role == "target":
            if nid not in end_ids_chosen:
                continue
            sig = _pattern_for_node(node)
            if sig is None:
                continue
            rows.append((nid, sig, boundary_end))
            continue
        if role == "intermediate" and nid in end_ids_chosen:
            sig = _pattern_for_node(node)
            if sig is None:
                continue
            rows.append((nid, sig, boundary_end))

    rows.sort(key=lambda t: (t[2], t[0], t[1]))
    return rows


def sync_macro_recipe_compiled_boundaries(
    macro: MacroRecipe, graph_document: dict[str, Any] | None
) -> None:
    """매크로의 compiled 경계 행을 교체한다. graph가 없거나 파생 불가면 빈 상태로 둔다."""

    macro.compiled_boundaries.all().delete()
    if not graph_document:
        return
    specs = compiled_boundary_specs_from_graph_document(graph_document)
    if not specs:
        return
    MacroRecipeCompiledBoundary.objects.bulk_create(
        [
            MacroRecipeCompiledBoundary(
                macro=macro,
                graph_shape_id=sid,
                pattern_signature=sig,
                boundary=bd,
            )
            for sid, sig, bd in specs
        ]
    )


__all__ = [
    "MAX_COMPILED_END_BOUNDARIES",
    "compiled_boundary_specs_from_graph_document",
    "sync_macro_recipe_compiled_boundaries",
]
