"""Feature-flagged JSONL latency traces for Asteroid Lab HTTP paths (output-only).

Enable with ``ASTEROID_LAB_PERF_TRACE=1``. Lines append under
``<BASE_DIR>/var/log/asteroid_lab_perf/lab_perf.jsonl`` (gitignored ``var/``).
"""

from __future__ import annotations

import contextvars
import json
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_write_lock = threading.Lock()
_active_var: contextvars.ContextVar[_Collector | None] = contextvars.ContextVar(
    "lab_perf_trace_active",
    default=None,
)


@dataclass
class _Collector:
    request_kind: str
    meta: dict[str, Any] = field(default_factory=dict)
    phases_ms: dict[str, float] = field(default_factory=dict)


def lab_perf_trace_enabled() -> bool:
    from django.conf import settings

    return bool(getattr(settings, "ASTEROID_LAB_PERF_TRACE", False))


def _repo_base_dir() -> Path:
    from django.conf import settings

    return Path(settings.BASE_DIR).resolve()


def lab_perf_trace_log_path() -> Path:
    return _repo_base_dir() / "var" / "log" / "asteroid_lab_perf" / "lab_perf.jsonl"


def record_perf_meta(**fields: Any) -> None:
    """Attach scalar metadata to the active request trace (no-op when disabled)."""

    active = _active_var.get()
    if active is None:
        return
    for key, value in fields.items():
        active.meta[key] = value


def record_perf_ms(phase: str, elapsed_ms: float) -> None:
    """Record a pre-measured phase duration in milliseconds."""

    active = _active_var.get()
    if active is None:
        return
    active.phases_ms[str(phase)] = float(elapsed_ms)


@contextmanager
def perf_span(phase: str) -> Iterator[None]:
    """Time one phase when a ``lab_perf_trace_request`` context is active."""

    active = _active_var.get()
    if active is None:
        yield
        return
    t0 = time.monotonic()
    try:
        yield
    finally:
        current = _active_var.get()
        if current is not None:
            current.phases_ms[str(phase)] = (time.monotonic() - t0) * 1000.0


@contextmanager
def lab_perf_trace_request(*, request_kind: str, **meta: Any) -> Iterator[None]:
    """Collect phase timings for one HTTP handler; emit one JSONL line on exit."""

    if not lab_perf_trace_enabled():
        yield
        return

    col = _Collector(request_kind=str(request_kind), meta=dict(meta))
    token = _active_var.set(col)
    t0 = time.monotonic()
    try:
        yield
    finally:
        col.phases_ms["total_ms"] = (time.monotonic() - t0) * 1000.0
        emit_lab_perf_trace(col)
        _active_var.reset(token)


def emit_lab_perf_trace(collector: _Collector) -> None:
    ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    record: dict[str, Any] = {
        "event": "asteroid_lab_perf",
        "ts": ts,
        "request_kind": collector.request_kind,
        **collector.phases_ms,
        **collector.meta,
    }
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    path = lab_perf_trace_log_path()
    with _write_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.open("a", encoding="utf-8").write(line)


def serialized_json_utf8_bytes(value: Any) -> int:
    """UTF-8 size of ``value`` as compact JSON (perf meta only; not solver input)."""

    if value is None:
        return 0
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def count_full_map_cells(frames: Sequence[Mapping[str, Any]]) -> int:
    """Cheap aggregate for perf records (not used by solver or replay logic)."""

    total = 0
    for frame in frames:
        fm = frame.get("full_map")
        if isinstance(fm, list):
            total += len(fm)
    return total


__all__ = [
    "count_full_map_cells",
    "emit_lab_perf_trace",
    "lab_perf_trace_enabled",
    "lab_perf_trace_log_path",
    "lab_perf_trace_request",
    "perf_span",
    "record_perf_meta",
    "record_perf_ms",
    "serialized_json_utf8_bytes",
]
