from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import TraceEvent
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    RecoveryTrigger,
    RejectedReason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.trace_semantics import (
    assert_no_replacement_route_not_commit_reason,
    assert_recovery_not_commit_reason,
    validate_trace_decision_semantics,
)


def _base_kwargs() -> dict[str, object]:
    return {
        "run_id": "r1",
        "phase": "p",
        "step_index": 0,
        "event_type": "t",
    }


def test_committed_false_with_commit_reason_raises() -> None:
    with pytest.raises(ValueError, match="committed=false"):
        TraceEvent(
            **_base_kwargs(),
            committed=False,
            commit_reason=CommitReason.NORMAL_GAIN,
            rejected_reason=None,
        )


def test_committed_true_without_commit_reason_raises() -> None:
    with pytest.raises(ValueError, match="committed=true requires"):
        TraceEvent(
            **_base_kwargs(),
            committed=True,
            commit_reason=None,
            rejected_reason=None,
        )


def test_committed_true_with_rejected_raises() -> None:
    with pytest.raises(ValueError, match="committed=true must not set"):
        TraceEvent(
            **_base_kwargs(),
            committed=True,
            commit_reason=CommitReason.NORMAL_GAIN,
            rejected_reason=RejectedReason.REJECTED_BY_OVERLAP,
        )


def test_recovery_trigger_string_rejected_as_commit_reason() -> None:
    with pytest.raises(ValueError, match="recovery_trigger value"):
        validate_trace_decision_semantics(
            committed=True,
            commit_reason=RecoveryTrigger.STEP4_ROUTING_FAILURE.value,
            rejected_reason=None,
        )


def test_rejected_by_no_replacement_route_rejected_as_commit_reason() -> None:
    with pytest.raises(ValueError, match="must never be used as commit_reason"):
        validate_trace_decision_semantics(
            committed=True,
            commit_reason=RejectedReason.REJECTED_BY_NO_REPLACEMENT_ROUTE.value,
            rejected_reason=None,
        )


def test_post_reclaim_trigger_never_commit_reason() -> None:
    with pytest.raises(ValueError, match="must never be used as commit_reason"):
        validate_trace_decision_semantics(
            committed=True,
            commit_reason=RecoveryTrigger.POST_RECLAIM_PASS3_CONNECTIVITY_BREAK.value,
            rejected_reason=None,
        )


def test_assert_recovery_not_commit_reason_helper() -> None:
    with pytest.raises(ValueError, match="RecoveryTrigger value rejected"):
        assert_recovery_not_commit_reason(RecoveryTrigger.FINAL_VALIDATION_FAILURE.value)


def test_assert_no_replacement_route_not_commit_reason_helper() -> None:
    with pytest.raises(ValueError, match="rejected_by_no_replacement_route"):
        assert_no_replacement_route_not_commit_reason(
            RejectedReason.REJECTED_BY_NO_REPLACEMENT_ROUTE.value,
        )


def test_valid_committed_trace_event() -> None:
    ev = TraceEvent(
        **_base_kwargs(),
        committed=True,
        commit_reason=CommitReason.DEGRADED_CONNECTED_RECOVERY,
        rejected_reason=None,
    )
    assert ev.committed is True
