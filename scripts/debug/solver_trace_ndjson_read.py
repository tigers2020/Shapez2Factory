"""Parse mining-layout NDJSON: legacy debug-wrapped ``kind: trace`` vs replay wire rows.

Replay wire (``trace_event`` output): ``{"location", "message", "data"}`` with optional
``data.run_id``. Legacy debug rows: ``{"kind": "trace", "message", "data", ...}``.
"""

from __future__ import annotations

from typing import Any


def run_id_matches_row(row: dict[str, Any], run_id: str | None) -> bool:
    """True if ``run_id`` is None or matches top-level ``run_id`` or ``data.run_id``."""

    if run_id is None:
        return True
    if row.get("run_id") == run_id:
        return True
    data = row.get("data")
    if isinstance(data, dict) and data.get("run_id") == run_id:
        return True
    return False


def row_trace_run_id(row: dict[str, Any]) -> str | None:
    """Correlation id for ``--split-by-ndjson-run-id`` (top-level wins, else ``data.run_id``)."""

    rid = row.get("run_id")
    if isinstance(rid, str) and rid:
        return rid
    data = row.get("data")
    if isinstance(data, dict):
        dr = data.get("run_id")
        if isinstance(dr, str) and dr:
            return dr
    return None


def extract_solver_summary_from_ndjson_row(
    row: dict[str, Any], *, run_id: str | None
) -> dict[str, Any] | None:
    """Return ``data.solver_summary`` dict if this row is a solver_summary trace line."""

    if not run_id_matches_row(row, run_id):
        return None
    if row.get("message") != "solver_summary":
        return None
    kind = row.get("kind")
    if kind is not None and kind != "trace":
        return None
    data = row.get("data")
    if not isinstance(data, dict):
        return None
    ss = data.get("solver_summary")
    return ss if isinstance(ss, dict) else None
