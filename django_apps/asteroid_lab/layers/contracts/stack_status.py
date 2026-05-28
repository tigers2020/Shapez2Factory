"""Stack run status codes for layer 2–5 orchestration."""

from __future__ import annotations

from enum import StrEnum


class StackRunStatus(StrEnum):
    SUCCESS = "success"
    TIMEOUT_FAIL_CLOSED = "timeout_fail_closed"
    LAYER_FAILED_CLOSED = "layer_failed_closed"
    VALIDATION_FAILED = "validation_failed"
