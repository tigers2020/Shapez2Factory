"""Request ID middleware contracts (PR-2)."""

from __future__ import annotations

import json
import logging

import pytest
from django.test import Client

from config.logging_json import JsonLogFormatter, RequestIdFilter, request_id_var
from django_apps.web.middleware.request_id import REQUEST_ID_HEADER


def _log_payload_after_request() -> dict[str, object]:
    record = logging.LogRecord(
        name="tests.request_id",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="after_request",
        args=(),
        exc_info=None,
    )
    RequestIdFilter().filter(record)
    return json.loads(JsonLogFormatter().format(record))


@pytest.mark.django_db
def test_response_includes_request_id_header() -> None:
    client = Client()
    response = client.get("/")
    assert REQUEST_ID_HEADER in response
    request_id = response[REQUEST_ID_HEADER]
    assert len(request_id) == 8
    assert all(c in "0123456789abcdef" for c in request_id)


@pytest.mark.django_db
def test_parallel_requests_get_distinct_request_ids() -> None:
    client = Client()
    id_a = client.get("/")[REQUEST_ID_HEADER]
    id_b = client.get("/")[REQUEST_ID_HEADER]
    assert id_a != id_b


@pytest.mark.django_db
def test_request_id_does_not_leak_after_middleware_returns() -> None:
    client = Client()
    client.get("/")
    payload = _log_payload_after_request()
    assert payload["request_id"] is None


def test_non_http_log_has_null_request_id() -> None:
    assert request_id_var.get() is None
    payload = _log_payload_after_request()
    assert payload["request_id"] is None


@pytest.mark.django_db
def test_inbound_request_id_header_is_ignored() -> None:
    client = Client()
    response = client.get("/", HTTP_X_REQUEST_ID="evil\ninjected")
    generated = response[REQUEST_ID_HEADER]
    assert generated != "evil\ninjected"
    assert "\n" not in generated
