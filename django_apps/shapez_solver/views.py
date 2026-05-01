from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.templatetags.static import static
from django.views.decorators.http import require_POST

from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_core.services.shape_render_scene import (
    ShapeRenderScene,
    build_shape_render_scene,
)
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverGraphNode,
    SolverOperationNode,
    SolverShapeNode,
)
from django_apps.shapez_solver.services.solver_service import (
    ShapeRef,
    SolverRequest,
    SolverResult,
    SolverService,
    SolveStep,
)


@require_POST
def solve_shape(request: HttpRequest) -> JsonResponse:
    code = _extract_shape_code(request)
    if code is None:
        return JsonResponse(
            {
                "ok": False,
                "found": False,
                "error": "Expected JSON object or form data with a 'code' field.",
                "warnings": [],
                "steps": [],
            },
            status=400,
        )

    stripped_code = code.strip()
    if not stripped_code:
        return JsonResponse(
            {
                "ok": False,
                "found": False,
                "error": "Shape code is empty.",
                "warnings": [],
                "steps": [],
            },
            status=400,
        )

    try:
        patterns = parse_shape_code_list(stripped_code)
    except ShapeCodeParseError as exc:
        return JsonResponse(
            {
                "ok": False,
                "found": False,
                "error": str(exc),
                "warnings": [],
                "steps": [],
            }
        )

    warnings: list[str] = []
    target_pattern = patterns[0]
    if target_pattern.raw_code != target_pattern.normalized_code:
        warnings.append(
            f"Pattern '{target_pattern.raw_code}' was normalized to "
            f"'{target_pattern.normalized_code}'."
        )
    if len(patterns) > 1:
        warnings.append("Multiple patterns were provided; only the first target was solved.")

    result = SolverService().solve(
        SolverRequest(
            target_pattern=target_pattern,
            max_depth=_extract_max_depth(request),
        )
    )
    payload = _serialize_solver_result(result, warnings=tuple(warnings))
    return JsonResponse(payload)


def _extract_shape_code(request: HttpRequest) -> str | None:
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        code = payload.get("code")
        return code if isinstance(code, str) else None

    code = request.POST.get("code")
    return code if code is not None else None


def _extract_max_depth(request: HttpRequest) -> int:
    value: Any
    if request.content_type == "application/json":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return 12
        value = payload.get("max_depth") if isinstance(payload, dict) else None
    else:
        value = request.POST.get("max_depth")

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 12
    return max(1, min(parsed, 64))


def _serialize_solver_result(
    result: SolverResult,
    warnings: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "ok": True,
        "found": result.found,
        "target": {
            "shape_code": result.target_shape,
            "normalized_code": result.target_shape,
        },
        "target_shape": result.target_shape,
        "warnings": [*warnings, *result.warnings],
        "steps": [_serialize_solver_step(step) for step in result.steps],
        "graph": _serialize_solver_graph(result.graph) if result.graph else None,
    }


def _serialize_solver_step(step: SolveStep) -> dict[str, Any]:
    operation = OPERATION_CATALOG[step.operation_type]
    return {
        "id": step.id,
        "index": step.index,
        "operation": {
            "type": operation.type.value,
            "label": operation.label,
            "icon": static(f"web/images/operations/{operation.icon}"),
            "input_count": operation.input_count,
            "output_count": operation.output_count,
            "description": operation.description,
        },
        "title": step.title,
        "description": step.description,
        "inputs": [_serialize_shape_ref(item) for item in step.inputs],
        "outputs": [_serialize_shape_ref(item) for item in step.outputs],
    }


def _serialize_shape_ref(item: ShapeRef) -> dict[str, Any]:
    pattern = parse_shape_code_list(item.shape_code)[0]
    scene = build_shape_render_scene(pattern)
    return {
        "shape_code": item.shape_code,
        "label": item.label,
        "preview_scene": _serialize_render_scene(scene),
    }


def _serialize_solver_graph(graph: SolverGraph) -> dict[str, Any]:
    return {
        "layout": {
            "direction": graph.direction,
        },
        "nodes": [_serialize_graph_node(node) for node in graph.nodes],
        "edges": [_serialize_graph_edge(edge) for edge in graph.edges],
    }


def _serialize_graph_node(node: SolverGraphNode) -> dict[str, Any]:
    if isinstance(node, SolverShapeNode):
        return {
            "id": node.id,
            "kind": node.kind,
            "role": node.role,
            "shape_code": node.shape_code,
            "label": node.label,
            "preview_scene": node.preview_scene or _build_preview_scene(node.shape_code),
            "reused_count": node.reused_count,
        }

    if isinstance(node, SolverOperationNode):
        return {
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

    raise TypeError(f"Unsupported graph node: {node!r}")


def _serialize_graph_edge(edge: SolverGraphEdge) -> dict[str, str | None]:
    return {
        "from": edge.from_id,
        "to": edge.to_id,
        "kind": edge.kind,
        "slot": edge.slot,
        "label": edge.label,
    }


def _build_preview_scene(shape_code: str) -> dict[str, Any]:
    pattern = parse_shape_code_list(shape_code)[0]
    return _serialize_render_scene(build_shape_render_scene(pattern))


def _serialize_render_scene(scene: ShapeRenderScene) -> dict[str, Any]:
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
