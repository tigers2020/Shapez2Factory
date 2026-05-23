"""Staff-only helpers shared by non-macro staff endpoints."""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from django_apps.web.models import ShapePartSprite


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
