from __future__ import annotations

from typing import Any

from django.templatetags.static import static

from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.services.factory_throughput_service import FactoryThroughputResult
from django_apps.shapez_solver.view_graph_serialization import serialize_solver_graph


def serialize_solver_result(
    result: FactoryThroughputResult,
    warnings: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "ok": True,
        "found": result.found,
        "target": {
            "shape_code": result.target_shape,
            "normalized_code": result.target_shape,
            "count": result.target_count,
        },
        "target_shape": result.target_shape,
        "base_demands": [serialize_base_demand(demand) for demand in result.base_demands],
        "warnings": [*warnings, *result.warnings],
        "steps": [serialize_solver_step(step) for step in result.steps],
        "graph": serialize_solver_graph(result.graph) if result.graph else None,
        "materialized_graph": (
            serialize_solver_graph(result.materialized_graph) if result.materialized_graph else None
        ),
    }


def serialize_base_demand(demand: Any) -> dict[str, Any]:
    return {
        "base_shape_code": demand.base_shape_code,
        "quadrants_per_target": demand.quadrants_per_target,
        "total_quadrants": demand.total_quadrants,
        "full_source_count": demand.full_source_count,
    }


def serialize_solver_step(step: Any) -> dict[str, Any]:
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
        "inputs": [serialize_shape_code(item) for item in step.input_shape_codes],
        "outputs": [serialize_shape_code(item) for item in step.output_shape_codes],
    }


def serialize_shape_code(shape_code: str) -> dict[str, Any]:
    from django_apps.shapez_solver.view_graph_serialization import build_preview_scene

    return {
        "shape_code": shape_code,
        "label": None,
        "preview_scene": build_preview_scene(shape_code),
    }


def error_payload(
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
