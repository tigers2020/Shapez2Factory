"""HTTP request correlation ID for ambient structured logging."""

from __future__ import annotations

import secrets
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from config.logging_json import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"


def _generate_request_id() -> str:
    return secrets.token_hex(4)


class RequestIdMiddleware:
    """Assign a local request_id per HTTP request; echo on response header."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = _generate_request_id()
        request.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response[REQUEST_ID_HEADER] = request_id
        return response
