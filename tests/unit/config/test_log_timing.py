"""log_timing helper contracts (PR-3)."""

from __future__ import annotations

import json
import logging
import re

from config.log_timing import log_timing
from config.logging_json import JsonLogFormatter, RequestIdFilter

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")


def _format_record(record: logging.LogRecord) -> dict[str, object]:
    RequestIdFilter().filter(record)
    return json.loads(JsonLogFormatter().format(record))


def test_log_timing_emits_ms_extra() -> None:
    logger = logging.getLogger("tests.log_timing")
    record_holder: list[logging.LogRecord] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            record_holder.append(record)

    handler = _CaptureHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        with log_timing(logger, "recipe_graph_recompute", node_count=3):
            pass
    finally:
        logger.removeHandler(handler)

    assert record_holder
    payload = _format_record(record_holder[0])
    assert payload["message"] == "recipe_graph_recompute"
    assert _SNAKE_CASE.match(str(payload["message"]))
    assert payload["node_count"] == 3
    assert isinstance(payload["ms"], float)
    assert float(payload["ms"]) >= 0
