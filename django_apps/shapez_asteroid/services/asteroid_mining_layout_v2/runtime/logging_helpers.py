"""Structured ``extra=`` payloads for solver runtime logs (no global config)."""

from __future__ import annotations

from typing import Any


def solver_phase_log_extra(*, run_id: str, phase: str) -> dict[str, Any]:
    """Return a dict suitable for ``logger.info(..., extra=…)``."""

    return {"run_id": run_id, "phase": phase}


__all__ = ["solver_phase_log_extra"]
