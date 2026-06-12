"""Console trace for Django-side Asteroid Lab solver invocations."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from shapez2_factory.adapters.asteroid_lab.cli_console import emit_cli_line


def _console_token(value: object) -> str:
    """Return a single-token value for access-log fields."""
    return str(value).strip().replace(" ", "_")


@contextmanager
def cli_invoke_trace(
    *,
    surface: str,
    command: str,
    slug: str,
) -> Iterator[dict[str]]:
    """Emit BA-9 start/end lines for a Django solver invocation."""

    emit_cli_line(f"{command} start", surface=surface, slug=slug)
    started = time.monotonic()
    fields: dict[str] = {
        "exit": 1,
        "ok": False,
    }
    try:
        yield fields
    except Exception as exc:
        fields.setdefault("error_code", _console_token(type(exc).__name__))
        raise
    finally:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        emit_cli_line(
            f"{command} end",
            surface=surface,
            slug=slug,
            exit=fields.get("exit"),
            elapsed_ms=elapsed_ms,
            solver_run_id=fields.get("solver_run_id"),
            error_code=fields.get("error_code"),
            ok=fields.get("ok"),
        )


__all__ = ["cli_invoke_trace"]
