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
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
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
from django_apps.shapez_solver.services.planner_service import UnsupportedTargetError
from django_apps.shapez_solver.services.solver_service import (
    SolverRequest,
    SolverResult,
    SolverService,
    SolverValidationError,
)
from django_apps.web.services.graph_preview import GraphPreviewRenderer, get_graph_preview_renderer


@require_POST
def solve_shape(request: HttpRequest) -> JsonResponse:
    code = _extract_shape_code(request)
    if code is None:
        return JsonResponse(
            _error_payload(
                "INVALID_REQUEST",
                "Expected JSON object or form data with a 'code' field.",
                {},
                (),
            ),
            status=400,
        )

    stripped_code = code.strip()
    if not stripped_code:
        return JsonResponse(
            _error_payload(
                "EMPTY_SHAPE_CODE",
                "Shape code is empty.",
                {},
                (),
            ),
            status=400,
        )

    try:
        patterns = parse_shape_code_list(stripped_code)
    except ShapeCodeParseError as exc:
        return JsonResponse(
            _error_payload(
                "SHAPE_CODE_PARSE_ERROR",
                str(exc),
                {"raw_code": stripped_code},
                (),
            )
        )

    warnings: list[str] = []
    target_pattern = patterns[0]
    target_shape = shape_from_pattern(target_pattern)
    if target_pattern.raw_code != target_pattern.normalized_code:
        warnings.append(
            f"Pattern '{target_pattern.raw_code}' was normalized to "
            f"'{target_pattern.normalized_code}'."
        )
    if len(patterns) > 1:
        warnings.append("Multiple patterns were provided; only the first target was solved.")

    try:
        result = SolverService().solve(
            SolverRequest(
                target_shape=target_shape,
                max_depth=_extract_max_depth(request),
            )
        )
    except UnsupportedTargetError as exc:
        return JsonResponse(
            _error_payload(
                exc.code,
                exc.message,
                exc.details or {"target_shape_code": target_shape.canonical_code},
                warnings,
            )
        )
    except SolverValidationError as exc:
        return JsonResponse(
            _error_payload(
                exc.code,
                "The generated recipe did not replay back to the requested target.",
                {
                    "expected": exc.expected,
                    "actual": exc.actual,
                },
                warnings,
            ),
            status=500,
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


def _serialize_solver_step(step: Any) -> dict[str, Any]:
    operation = OPERATION_CATALOG[step.operation_type]
    return {
        "id": step.id,
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
        "inputs": [_serialize_shape_code(item) for item in step.input_shape_codes],
        "outputs": [_serialize_shape_code(item) for item in step.output_shape_codes],
    }


def _serialize_shape_code(shape_code: str) -> dict[str, Any]:
    preview_scene = _serialize_render_scene(
        build_shape_render_scene(parse_shape_code_list(shape_code)[0])
    )
    return {
        "shape_code": shape_code,
        "label": None,
        "preview_scene": preview_scene,
    }


def _serialize_solver_graph(graph: SolverGraph) -> dict[str, Any]:
    preview_renderer = get_graph_preview_renderer()
    return {
        "layout": {
            "direction": graph.direction,
        },
        "nodes": [_serialize_graph_node(node, preview_renderer) for node in graph.nodes],
        "edges": [_serialize_graph_edge(edge) for edge in graph.edges],
    }


def _serialize_graph_node(
    node: SolverGraphNode,
    preview_renderer: GraphPreviewRenderer,
) -> dict[str, Any]:
    if isinstance(node, SolverShapeNode):
        preview_scene = node.preview_scene or _build_preview_scene(node.shape_code)
        graph_preview = preview_renderer.render(preview_scene)
        return {
            "id": node.id,
            "kind": node.kind,
            "role": node.role,
            "shape_code": node.shape_code,
            "label": node.label,
            "preview_scene": preview_scene,
            "preview_markup": graph_preview.markup,
            "preview_image_url": graph_preview.image_url,
            "preview_alt": graph_preview.alt_text,
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


def _error_payload(
    code: str,
    message: str,
    details: dict[str, str],
    warnings: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    return {
        "ok": False,
        "found": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "warnings": list(warnings),
        "steps": [],
    }
