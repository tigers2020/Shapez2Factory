"""CLI console observability formatter (BA-9, spec §11).

Emits **one access-log-style line per CLI event** to ``sys.stderr`` so developers
see start/end one-liners in the same terminal as ``runserver``. This is an
*output-only* observability surface (same class as ``lab_perf_trace`` JSONL); it
is **never** solver input and never mixed into artifact payloads or JSON bodies.

BA-1 placement: this module is part of the pure core
(``src/shapez2_factory/**``) and uses **stdlib only** — it must never import
Django, the Django apps, or project settings.
"""

from __future__ import annotations

import os
import sys
import time

ENV_CONSOLE_LOG = "ASTEROID_LAB_CLI_CONSOLE_LOG"
ENV_VERBOSE_LOG = "ASTEROID_LAB_CLI_VERBOSE"

# Master-switch values that disable console logging (case-insensitive, stripped).
# Every other value — including unset, ``1``, ``true`` or empty-but-set — keeps it on.
_DISABLED_VALUES = frozenset({"0", "false", "no"})

_TIMESTAMP_FORMAT = "%d/%b/%Y %H:%M:%S"


def console_logging_enabled() -> bool:
    """Return whether BA-9 stderr one-liners should be emitted.

    Default ON. Disabled only when ``ASTEROID_LAB_CLI_CONSOLE_LOG`` (stripped,
    lower-cased) is one of ``0`` / ``false`` / ``no``.
    """
    raw = os.environ.get(ENV_CONSOLE_LOG)
    if raw is None:
        return True
    return raw.strip().lower() not in _DISABLED_VALUES


def verbose_logging_enabled() -> bool:
    """Return whether optional per-layer CLI lines should be emitted."""

    raw = os.environ.get(ENV_VERBOSE_LOG)
    if raw is None:
        return False
    return raw.strip().lower() not in _DISABLED_VALUES


def _render_value(value: object) -> str:
    # Booleans render lowercase (``ok=true`` / ``ok=false``) per spec.
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def emit_cli_line(event: str, *, now: float | None = None, **fields: object) -> None:
    """Write a single BA-9 line to ``sys.stderr`` (no-op when logging disabled).

    Format: ``[DD/Mon/YYYY HH:MM:SS] asteroid_cli <event> key=value …``

    * ``now`` is an optional epoch seconds value (``time.monotonic`` is not used
      here — wall-clock for the human-readable timestamp). Injectable so tests
      are deterministic; ``None`` means current local time.
    * ``fields`` render as space-joined ``key=value`` in the given order.
    * Fields whose value is ``None`` are omitted (null omission, spec §11).

    Field values are assumed to be single tokens (no embedded spaces); space is
    the field separator, so a whitespace-bearing value would render an
    unparseable line. Current callers only pass ints/bools/safe ``run_key``
    values. Revisit quoting if free-form fields (slug, messages) land in 3b/4.
    """
    if not console_logging_enabled():
        return
    timestamp = time.strftime(_TIMESTAMP_FORMAT, time.localtime(now))
    parts = [f"[{timestamp}] asteroid_cli {event}"]
    for key, value in fields.items():
        if value is None:
            continue
        parts.append(f"{key}={_render_value(value)}")
    print(" ".join(parts), file=sys.stderr)


__all__ = [
    "ENV_CONSOLE_LOG",
    "ENV_VERBOSE_LOG",
    "console_logging_enabled",
    "emit_cli_line",
    "verbose_logging_enabled",
]
