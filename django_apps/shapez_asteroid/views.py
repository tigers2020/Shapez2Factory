from __future__ import annotations

import json

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from django_apps.shapez_asteroid.services.asteroid_map_cells import (
    list_map_cells_json,
    parse_bbox,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    build_copy_preview_mining,
)
from django_apps.shapez_asteroid.services.copy_preview_debug_dump import (
    dump_copy_preview_debug,
)
from django_apps.shapez_asteroid.services.style_classifier import asteroid_map_style_catalog
from django_apps.shapez_core.services.shapez_copy_decode import (
    ShapezCopyDecodeError,
    decode_shapez2_copy,
)


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_GET
def map_cells(request: HttpRequest) -> JsonResponse:
    err, bbox = parse_bbox(request.GET)
    if err is not None:
        return JsonResponse(err, status=400)
    assert bbox is not None
    x_min, x_max, y_min, y_max = bbox
    return JsonResponse(list_map_cells_json(x_min, x_max, y_min, y_max))


@require_POST
def copy_preview(request: HttpRequest) -> JsonResponse:
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    code = body.get("code")
    if not isinstance(code, str):
        return JsonResponse({"ok": False, "error": "code must be a string"}, status=400)

    try:
        decoded = decode_shapez2_copy(code)
    except ShapezCopyDecodeError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    debug_dir = getattr(settings, "SHAPEZ_COPY_DEBUG_DIR", "") or ""
    if debug_dir:
        dump_copy_preview_debug(code, decoded, debug_dir)

    summary, mining_map = build_copy_preview_mining(decoded)
    return JsonResponse(
        {
            "ok": True,
            "summary": summary,
            "mining_map": mining_map,
            "style_catalog": asteroid_map_style_catalog(),
        }
    )
