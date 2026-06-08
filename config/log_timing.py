"""Context manager for structured timing logs (ambient JSON file handlers)."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


@contextmanager
def log_timing(logger: logging.Logger, event: str, /, **extra: Any) -> Iterator[None]:
    """Log ``event`` with ``ms`` in extra after the block completes."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(event, extra={**extra, "ms": elapsed_ms})
