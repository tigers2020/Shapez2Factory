"""Normalize ``commit_reason`` / ``rejected_reason`` / ``recovery_trigger`` telemetry namespaces."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INVALID_COMMIT_REASON_STRINGS,
    RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
    ROLLUP_COMMIT_REASONS_CANONICAL,
)

__all__ = [
    "partition_pass3_commit_reason_payload",
    "rollup_return_reason_to_recovery_trigger",
]

# Pipeline ``return_reason`` values that are **not** Pass3 candidate rejections; map into rollup
# ``recovery_trigger`` when no explicit bounded trigger is already present.
_RETURN_REASON_TO_RECOVERY_TRIGGER: dict[str, str] = {
    "validation_connectivity_failed": RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
    "validation_geometry_failed": RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
    "validation_unfinalized_placement_failed": RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
}


def rollup_return_reason_to_recovery_trigger(return_reason: str | None) -> str | None:
    """Map solver ``return_reason`` to a rollup ``recovery_trigger``, or ``None``."""

    if not return_reason:
        return None
    return _RETURN_REASON_TO_RECOVERY_TRIGGER.get(str(return_reason).strip())


def partition_pass3_commit_reason_payload(
    raw: Any,
    *,
    pass3_committed: bool,
    pass3_final_committed: bool,
) -> tuple[str | None, str | None]:
    """Split ``commit_reason``-shaped telemetry into (canonical success commit, promoted reject).

    Returns ``(commit_reason_or_none, pass3_rejected_reason_promotion_or_none)``.
    Mis-filed rejection-shaped strings under ``commit_reason`` are promoted to the reject bucket
    when ``pass3_committed`` and ``pass3_final_committed`` are both true.
    """

    if not pass3_committed or not pass3_final_committed:
        return None, None
    if raw is None:
        return None, None
    cr_s = str(raw).strip() if isinstance(raw, str) else str(raw).strip()
    if not cr_s:
        return None, None
    if cr_s in INVALID_COMMIT_REASON_STRINGS:
        if cr_s.startswith("rejected_by") or "rejected_" in cr_s:
            return None, cr_s
        return None, None
    if cr_s in ROLLUP_COMMIT_REASONS_CANONICAL:
        return cr_s, None
    return None, None
