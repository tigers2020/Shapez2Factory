from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from django_apps.shapez_core.services.preview_service import build_shape_preview_response


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_GET
def shape_preview(request: HttpRequest) -> JsonResponse:
    code = request.GET.get("code", "")
    payload, status_code = build_shape_preview_response(code=code)
    return JsonResponse(payload, status=status_code)
