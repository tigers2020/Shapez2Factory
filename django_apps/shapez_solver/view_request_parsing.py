from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest


def extract_shape_code(request: HttpRequest) -> str | None:
    payload = extract_json_payload(request)
    if request.content_type == "application/json":
        if payload is None:
            return None
        code = payload.get("code")
        return code if isinstance(code, str) else None

    code = request.POST.get("code")
    return code if code is not None else None


def extract_max_depth(request: HttpRequest) -> int:
    value: Any
    payload = extract_json_payload(request)
    if request.content_type == "application/json":
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


def extract_target_count(request: HttpRequest) -> int:
    value: Any
    payload = extract_json_payload(request)
    if request.content_type == "application/json":
        value = None if payload is None else payload.get("target_count")
    else:
        value = request.POST.get("target_count")

    if value in (None, ""):
        return 1

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("target_count must be an integer greater than or equal to 1") from exc
    if parsed < 1:
        raise ValueError("target_count must be greater than or equal to 1")
    return parsed


def extract_json_payload(request: HttpRequest) -> dict[str, Any] | None:
    if request.content_type != "application/json":
        return None
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
