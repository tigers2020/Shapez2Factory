"""Structured JSON logging for ambient stdlib loggers (file handlers only)."""

from __future__ import annotations

import contextvars
import json
import logging
from datetime import UTC, datetime

BASE_PAYLOAD_KEYS = frozenset({"ts", "level", "logger", "message", "request_id"})

LOG_RECORD_RESERVED_KEYS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "ambient_log_request_id",
    default=None,
)


class RequestIdFilter(logging.Filter):
    """Attach request_id from ContextVar to each log record (handler-level)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonLogFormatter(logging.Formatter):
    """Emit one JSON object per log record (no trailing newline — handler owns terminator)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }

        for key, value in record.__dict__.items():
            if key in BASE_PAYLOAD_KEYS or key in LOG_RECORD_RESERVED_KEYS:
                continue
            if key.startswith("_"):
                continue
            payload[key] = value

        return json.dumps(payload, ensure_ascii=False, default=str)
