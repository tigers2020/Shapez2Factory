from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest

_JSON_CONTENT_TYPE = "application/json"


def extract_shape_code(request: HttpRequest) -> str | None:
    payload = extract_json_payload(request)
    if request.content_type == _JSON_CONTENT_TYPE:
        if payload is None:
            return None
        code = payload.get("code")
        return code if isinstance(code, str) else None

    code = request.POST.get("code")
    return code if code is not None else None


def extract_max_depth(request: HttpRequest) -> int:
    value: Any
    payload = extract_json_payload(request)
    if request.content_type == _JSON_CONTENT_TYPE:
        if payload is None:
            return 12
        value = payload.get("max_depth")
    else:
        value = request.POST.get("max_depth")

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 12
    return max(1, min(parsed, 64))


def extract_json_payload(request: HttpRequest) -> dict[str, Any] | None:
    if request.content_type != _JSON_CONTENT_TYPE:
        return None
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
