"""
Trace / replay decision semantics (§13.5, §16.3).

No log/NDJSON parsing — validates in-memory DTO fields only.

**Not enforced** (pending explicit spec / product agreement before tightening):

- ``committed=false`` does not require ``rejected_reason`` or ``rollback_reason`` to be set.
- ``committed=false`` does not forbid both ``rejected_reason`` and ``rollback_reason`` set.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    TransportKind,
)

_RECOVERY_VALUES = frozenset(m.value for m in RecoveryTrigger)
_FORBIDDEN_COMMIT_STRINGS = frozenset(
    {
        RecoveryTrigger.POST_RECLAIM_PASS3_CONNECTIVITY_BREAK.value,
        RejectedReason.REJECTED_BY_NO_REPLACEMENT_ROUTE.value,
    }
)


def validate_trace_decision_semantics(
    *,
    committed: bool,
    commit_reason: CommitReason | str | None,
    rejected_reason: RejectedReason | str | None,
    rollback_reason: RollbackReason | str | None = None,
) -> None:
    """
    Critical contracts:
    1. ``commit_reason`` only when ``committed`` is true.
    2. ``committed`` false must not set ``commit_reason`` (use reject/rollback).
    3. Recovery trigger strings are never ``commit_reason``.
    4. ``post_reclaim_pass3_connectivity_break`` and ``rejected_by_no_replacement_route``
       must never be commit reasons.
    """
    rr = _optional_enum_str(rejected_reason)
    rb = _optional_enum_str(rollback_reason)

    if committed:
        if rr is not None or rb is not None:
            msg = "committed=true must not set rejected_reason or rollback_reason"
            raise ValueError(msg)
        if commit_reason is None:
            msg = "committed=true requires commit_reason (CommitReason)"
            raise ValueError(msg)
        cr = _commit_reason_to_str(commit_reason)
        if cr in _FORBIDDEN_COMMIT_STRINGS:
            msg = f"{cr!r} must never be used as commit_reason"
            raise ValueError(msg)
        if cr in _RECOVERY_VALUES:
            msg = "recovery_trigger value is not a valid commit_reason"
            raise ValueError(msg)
        if not _is_valid_commit_reason(cr):
            msg = f"invalid commit_reason: {commit_reason!r}"
            raise ValueError(msg)
    else:
        if commit_reason is not None:
            msg = (
                "committed=false must not set commit_reason; "
                "use rejected_reason or rollback_reason"
            )
            raise ValueError(msg)


def _optional_enum_str(value: RollbackReason | RejectedReason | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (RollbackReason, RejectedReason)):
        out: str = value.value
        return out
    if isinstance(value, str):
        return value
    msg = f"unexpected reject/rollback label type: {type(value)!r}"
    raise TypeError(msg)


def _commit_reason_to_str(commit_reason: CommitReason | str) -> str:
    if isinstance(commit_reason, CommitReason):
        return commit_reason.value
    return str(commit_reason)


def _is_valid_commit_reason(value: str) -> bool:
    return value in frozenset(m.value for m in CommitReason)


def assert_recovery_not_commit_reason(candidate: str) -> None:
    """Explicit guard: a recovery trigger label must not appear as commit_reason."""
    if candidate in _RECOVERY_VALUES:
        msg = "RecoveryTrigger value rejected as CommitReason"
        raise ValueError(msg)


def assert_no_replacement_route_not_commit_reason(candidate: str) -> None:
    if candidate == RejectedReason.REJECTED_BY_NO_REPLACEMENT_ROUTE.value:
        msg = "rejected_by_no_replacement_route rejected as CommitReason"
        raise ValueError(msg)


def validate_route_level_trace_transport(
    *,
    route_level: bool,
    transport_kind: TransportKind | str | None,
) -> None:
    """§16.3: ``batch_mixed`` is only for batched belt+pipe records, not per-route events."""

    if not route_level:
        return
    if transport_kind is None or transport_kind == "none":
        return
    if isinstance(transport_kind, TransportKind):
        tk = transport_kind.value
    else:
        tk = str(transport_kind)
    if tk == "batch_mixed":
        msg = "batch_mixed is not allowed for route-level TraceEvent"
        raise ValueError(msg)
