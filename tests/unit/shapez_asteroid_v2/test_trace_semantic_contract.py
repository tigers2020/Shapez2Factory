"""Domain ``TraceEvent`` + ``trace_semantics`` contracts (§16.3, §13.5)."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    TraceEvent,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.trace_semantics import (
    validate_trace_decision_semantics,
)


def _base_trace_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "run_id": "r1",
        "phase": "step4",
        "step_index": 0,
        "event_type": "route_try",
        "committed": True,
        "commit_reason": CommitReason.NORMAL_GAIN,
        "rejected_reason": None,
        "rollback_reason": None,
    }
    base.update(overrides)
    return base


def test_committed_false_with_commit_reason_raises() -> None:
    with pytest.raises(ValueError, match="committed=false must not set commit_reason"):
        TraceEvent(**_base_trace_kwargs(committed=False, commit_reason=CommitReason.NORMAL_GAIN))


def test_committed_true_without_commit_reason_raises() -> None:
    with pytest.raises(ValueError, match="committed=true requires commit_reason"):
        TraceEvent(**_base_trace_kwargs(commit_reason=None))


def test_recovery_trigger_string_rejected_as_commit_reason() -> None:
    with pytest.raises(ValueError, match="recovery_trigger value is not a valid commit_reason"):
        TraceEvent(
            **_base_trace_kwargs(commit_reason=RecoveryTrigger.STEP4_ROUTING_FAILURE.value)  # type: ignore[arg-type]
        )


def test_rejected_by_no_replacement_route_rejected_as_commit_reason() -> None:
    with pytest.raises(ValueError, match="must never be used as commit_reason"):
        TraceEvent(
            **_base_trace_kwargs(
                commit_reason=RejectedReason.REJECTED_BY_NO_REPLACEMENT_ROUTE.value  # type: ignore[arg-type]
            )
        )


def test_invalid_commit_reason_string_raises() -> None:
    with pytest.raises(ValueError, match="invalid commit_reason"):
        TraceEvent(
            **_base_trace_kwargs(commit_reason="not_a_real_commit_reason")  # type: ignore[arg-type]
        )


def test_committed_false_without_reject_or_rollback_ok() -> None:
    """Current contract: only ``commit_reason`` is forbidden when ``committed`` is false."""
    ev = TraceEvent(
        **_base_trace_kwargs(
            committed=False,
            commit_reason=None,
            rejected_reason=None,
            rollback_reason=None,
        )
    )
    assert ev.committed is False
    assert ev.rejected_reason is None
    assert ev.rollback_reason is None


def test_committed_false_with_both_reject_and_rollback_ok() -> None:
    """Not XOR-enforced today; documents allowed combination for regression if policy tightens."""
    ev = TraceEvent(
        **_base_trace_kwargs(
            committed=False,
            commit_reason=None,
            rejected_reason=RejectedReason.REJECTED_BY_OVERLAP,
            rollback_reason=RollbackReason.ROLLBACK_UNROUTED_PLACEMENT,
        )
    )
    assert ev.rejected_reason is RejectedReason.REJECTED_BY_OVERLAP
    assert ev.rollback_reason is RollbackReason.ROLLBACK_UNROUTED_PLACEMENT


def test_route_level_batch_mixed_raises() -> None:
    with pytest.raises(ValueError, match="batch_mixed is not allowed for route-level"):
        TraceEvent(
            **_base_trace_kwargs(
                route_level=True,
                transport_kind="batch_mixed",
            )
        )


def test_route_level_shape_belt_ok() -> None:
    ev = TraceEvent(
        **_base_trace_kwargs(
            route_level=True,
            transport_kind=TransportKind.SHAPE_BELT,
        )
    )
    assert ev.transport_kind is TransportKind.SHAPE_BELT


def test_non_route_batch_mixed_ok() -> None:
    ev = TraceEvent(
        **_base_trace_kwargs(
            route_level=False,
            transport_kind="batch_mixed",
        )
    )
    assert ev.transport_kind == "batch_mixed"


def test_validate_trace_decision_committed_false_reject_ok() -> None:
    validate_trace_decision_semantics(
        committed=False,
        commit_reason=None,
        rejected_reason=RejectedReason.REJECTED_BY_OVERLAP,
        rollback_reason=None,
    )


def test_validate_trace_decision_committed_true_with_reject_raises() -> None:
    with pytest.raises(ValueError, match="committed=true must not set rejected"):
        validate_trace_decision_semantics(
            committed=True,
            commit_reason=CommitReason.NORMAL_GAIN,
            rejected_reason=RejectedReason.REJECTED_BY_OVERLAP,
            rollback_reason=None,
        )
