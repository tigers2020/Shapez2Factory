"""Structured ambient JSON logging contracts (PR-1)."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from config.logging_json import JsonLogFormatter, RequestIdFilter, request_id_var


def _make_record(
    logger_name: str = "test.logger",
    msg: str = "test_event",
    level: int = logging.INFO,
    *,
    extra: dict[str, object] | None = None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=logger_name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    if extra:
        for key, value in extra.items():
            setattr(record, key, value)
    return record


def test_json_formatter_required_keys() -> None:
    formatter = JsonLogFormatter()
    record = _make_record()
    RequestIdFilter().filter(record)

    payload = json.loads(formatter.format(record))
    assert set(payload.keys()) >= {"ts", "level", "logger", "message", "request_id"}
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "test_event"
    assert payload["request_id"] is None


def test_json_formatter_no_trailing_newline() -> None:
    formatter = JsonLogFormatter()
    record = _make_record()
    RequestIdFilter().filter(record)

    formatted = formatter.format(record)
    assert not formatted.endswith("\n")


def test_handler_emit_no_blank_jsonl_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "test.log"
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=1)
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(RequestIdFilter())

    logger = logging.getLogger("tests.unit.config.test_logging_json.handler")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        logger.info("first_event")
        logger.info("second_event", extra={"gene_key": "abc"})
    finally:
        handler.close()
        logger.removeHandler(handler)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert lines
    assert all(line.strip() for line in lines)
    for line in lines:
        json.loads(line)


def test_extra_promoted_to_top_level() -> None:
    formatter = JsonLogFormatter()
    record = _make_record(extra={"gene_key": "abc"})
    RequestIdFilter().filter(record)

    payload = json.loads(formatter.format(record))
    assert payload["gene_key"] == "abc"


def test_collision_extra_keys_dropped() -> None:
    formatter = JsonLogFormatter()
    record = _make_record(msg="real_message", extra={"message": "override", "level": "fake"})
    RequestIdFilter().filter(record)

    payload = json.loads(formatter.format(record))
    assert payload["message"] == "real_message"
    assert payload["level"] == "INFO"
    assert "override" not in payload.values()
    assert "fake" not in payload.values()


def test_non_primitive_extra_does_not_crash() -> None:
    formatter = JsonLogFormatter()
    record = _make_record(extra={"path": Path("x/y")})
    RequestIdFilter().filter(record)

    payload = json.loads(formatter.format(record))
    assert payload["path"] == str(Path("x/y"))


def test_log_record_reserved_keys_not_leaked() -> None:
    formatter = JsonLogFormatter()
    record = _make_record()
    RequestIdFilter().filter(record)

    payload = json.loads(formatter.format(record))
    assert "pathname" not in payload
    assert "lineno" not in payload
    assert "msg" not in payload


def test_request_id_filter_uses_contextvar() -> None:
    token = request_id_var.set("abcd1234")
    try:
        record = _make_record()
        RequestIdFilter().filter(record)
        formatter = JsonLogFormatter()
        payload = json.loads(formatter.format(record))
        assert payload["request_id"] == "abcd1234"
    finally:
        request_id_var.reset(token)


@pytest.mark.django_db
def test_settings_logging_config_when_file_log_enabled(settings) -> None:
    assert settings.LOGGING
    assert "json_file" in settings.LOGGING["formatters"]
    assert "solver_file" in settings.LOGGING["handlers"]
    assert "django_apps.shapez_solver" in settings.LOGGING["loggers"]
    assert "django_apps.asteroid_lab.services" in settings.LOGGING["loggers"]
