"""Typed semantic namespaces for recovery / commit / rollback telemetry."""

from __future__ import annotations

from typing import Any, Literal, TypeGuard

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import (
    constants as fc,
)

type RecoveryTrigger = Literal[
    "step4_routing_failure",
    "step4_capacity_failure",
    "pass3_connectivity_break",
    "reclaim_incremental_failure",
    "post_reclaim_pass3_connectivity_break",
    "validation_recovery",
    "final_validation_failure",
]
type CommitReason = Literal["normal_gain", "degraded_connected_recovery"]
type RollbackReason = str
type RejectedReason = str

RECOVERY_TRIGGER_VALUES: frozenset[str] = frozenset(
    {
        fc.RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
        fc.RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
        fc.RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK,
        fc.RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE,
        fc.RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
        fc.RECOVERY_TRIGGER_VALIDATION_RECOVERY_ENTRY,
        fc.RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
    }
)
COMMIT_REASON_VALUES: frozenset[str] = frozenset(fc.ROLLUP_COMMIT_REASONS_CANONICAL)
INVALID_COMMIT_REASON_VALUES: frozenset[str] = frozenset(fc.INVALID_COMMIT_REASON_STRINGS)


def _non_empty_string(raw: Any) -> str | None:
    if raw is None:
        return None
    out = str(raw).strip()
    return out or None


def is_recovery_trigger(raw: Any) -> TypeGuard[RecoveryTrigger]:
    """True if ``raw`` belongs to the recovery-trigger namespace."""

    s = _non_empty_string(raw)
    return s in RECOVERY_TRIGGER_VALUES if s is not None else False


def is_commit_reason(raw: Any) -> TypeGuard[CommitReason]:
    """True only for successful commit reasons."""

    s = _non_empty_string(raw)
    return s in COMMIT_REASON_VALUES if s is not None else False


def is_invalid_commit_reason(raw: Any) -> bool:
    """True for known reject/rollback/trigger strings misfiled as ``commit_reason``."""

    s = _non_empty_string(raw)
    return s in INVALID_COMMIT_REASON_VALUES if s is not None else False


def normalize_success_commit_reason(raw: Any) -> CommitReason | None:
    """Return a typed success commit reason, or ``None`` for all other namespaces."""

    if not is_commit_reason(raw):
        return None
    return raw


def promote_misfiled_rejected_reason(raw: Any) -> RejectedReason | None:
    """Recover reject-shaped strings found in a legacy ``commit_reason`` slot."""

    s = _non_empty_string(raw)
    if s is None or not is_invalid_commit_reason(s):
        return None
    if s.startswith("rejected_by") or "rejected_" in s:
        return s
    return None


__all__ = [
    "COMMIT_REASON_VALUES",
    "CommitReason",
    "INVALID_COMMIT_REASON_VALUES",
    "RECOVERY_TRIGGER_VALUES",
    "RecoveryTrigger",
    "RejectedReason",
    "RollbackReason",
    "is_commit_reason",
    "is_invalid_commit_reason",
    "is_recovery_trigger",
    "normalize_success_commit_reason",
    "promote_misfiled_rejected_reason",
]
