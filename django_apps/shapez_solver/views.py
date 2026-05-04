from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.services.factory_throughput_service import (
    FactoryThroughputRequest,
    FactoryThroughputService,
)
from django_apps.shapez_solver.services.planner_service import UnsupportedTargetError
from django_apps.shapez_solver.view_request_parsing import (
    extract_max_depth,
    extract_shape_code,
    extract_solver_timeout_seconds,
)
from django_apps.shapez_solver.view_serialization import error_payload, serialize_solver_result


@require_POST
def solve_shape(request: HttpRequest) -> JsonResponse:
    code = extract_shape_code(request)
    if code is None:
        return JsonResponse(
            error_payload(
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
            error_payload(
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
            error_payload(
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
        result = FactoryThroughputService().solve(
            FactoryThroughputRequest(
                target_shape=target_shape,
                max_depth=extract_max_depth(request),
                solver_timeout_seconds=extract_solver_timeout_seconds(request),
            )
        )
    except UnsupportedTargetError as exc:
        return JsonResponse(
            error_payload(
                exc.code,
                exc.message,
                exc.details or {"target_shape_code": target_shape.canonical_code},
                warnings,
            )
        )
    payload = serialize_solver_result(result, warnings=tuple(warnings))
    return JsonResponse(payload)
