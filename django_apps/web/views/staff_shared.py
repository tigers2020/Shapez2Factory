"""Staff-only helpers shared by non-macro staff endpoints."""

from __future__ import annotations

import json
from functools import wraps
from typing import Any

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from django_apps.web.models import ShapePartSprite
from django_apps.web.services.graph_preview import PlaywrightPngGraphPreviewRenderer


def staff_site_required(view_func):
    """Require login at ``settings.LOGIN_URL`` and ``is_staff`` (403 if logged-in but not staff)."""

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def _parse_graph_preview_warm_body(
    request: HttpRequest,
) -> tuple[str, dict[str, Any]] | JsonResponse:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False}, status=400)
    if not isinstance(body, dict):
        return JsonResponse({"ok": False}, status=400)
    cache_key = body.get("cache_key")
    preview_scene = body.get("preview_scene")
    if not isinstance(cache_key, str) or not isinstance(preview_scene, dict):
        return JsonResponse({"ok": False}, status=400)
    return cache_key, preview_scene


@staff_site_required
@require_http_methods(["POST"])
def macro_pattern_staff_api_graph_preview_warm(request: HttpRequest) -> JsonResponse:
    """Warm one graph-preview PNG (staff-only; validates cache_key against preview_scene)."""
    parsed = _parse_graph_preview_warm_body(request)
    if isinstance(parsed, JsonResponse):
        return parsed
    cache_key, preview_scene = parsed
    renderer = PlaywrightPngGraphPreviewRenderer()
    expected_key = renderer.cache_key(preview_scene)
    if cache_key != expected_key:
        return JsonResponse({"ok": False}, status=400)
    preview = renderer.render(preview_scene)
    return JsonResponse(
        {
            "ok": True,
            "cache_key": expected_key,
            "preview_image_url": preview.image_url or "",
        }
    )


@staff_site_required
@require_http_methods(["GET"])
def shape_part_sprite_manifest(request: HttpRequest) -> JsonResponse:
    """JSON manifest of baked atomic part PNGs (for recipe graph tile Canvas2D composition)."""
    renderer_version = (request.GET.get("renderer_version") or "v1").strip()
    sprites: dict[str, dict[str, int | str]] = {}
    qs = ShapePartSprite.objects.filter(renderer_version=renderer_version).order_by(
        "sprite_key",
    )
    for row in qs:
        sprites[row.sprite_key] = {
            "url": row.image.url,
            "width": row.image_width,
            "height": row.image_height,
        }
    return JsonResponse({"renderer_version": renderer_version, "sprites": sprites})
