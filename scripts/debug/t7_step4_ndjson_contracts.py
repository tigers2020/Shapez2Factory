"""Pure helper contracts for T7 STEP4 NDJSON verification."""

from __future__ import annotations

from typing import Any


def _coerce_int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def failure_detail_count_contract(
    *,
    fail_details: list[dict[str, Any]],
    solver_summary: dict[str, Any],
    step4_completed_data: dict[str, Any],
) -> dict[str, Any]:
    """Compare final summary detail count against the final STEP4 reentry rows.

    Debug NDJSON is a raw stage stream. A bounded STEP4 reentry can leave both the
    first STEP4 attempt and the final reentry attempt in the file, while
    ``solver_summary`` describes the final returned STEP4 result.
    """

    summary_count = _coerce_int_or_none(solver_summary.get("step4_failure_details_count")) or 0
    final_reentry_index = _coerce_int_or_none(step4_completed_data.get("step4_reentry_index"))
    if final_reentry_index is None:
        final_reentry_details = list(fail_details)
    else:
        final_reentry_details = [
            det
            for det in fail_details
            if _coerce_int_or_none(det.get("step4_reentry_index")) == final_reentry_index
        ]
    return {
        "summary_count": int(summary_count),
        "raw_detail_count": int(len(fail_details)),
        "final_reentry_index": final_reentry_index,
        "final_reentry_detail_count": int(len(final_reentry_details)),
        "matches_final_reentry": int(summary_count) == len(final_reentry_details),
    }
