"""Regression: commit_reason / rejected_reason / recovery_trigger telemetry namespaces."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.recovery_semantics import (
    COMMIT_REASON_VALUES,
    INVALID_COMMIT_REASON_VALUES,
    RECOVERY_TRIGGER_VALUES,
    is_commit_reason,
    is_invalid_commit_reason,
    is_recovery_trigger,
    normalize_success_commit_reason,
    promote_misfiled_rejected_reason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import (
    constants as fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    synthesize_recovery_validation_outcome,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.semantic_contracts import (
    partition_pass3_commit_reason_payload,
)


def test_partition_committed_false_never_emits_commit_reason() -> None:
    c, r = partition_pass3_commit_reason_payload(
        fc.P3F_COMMIT_REASON_NORMAL_GAIN,
        pass3_committed=False,
        pass3_final_committed=True,
    )
    assert c is None and r is None


def test_partition_post_reclaim_connectivity_break_never_commit() -> None:
    c, r = partition_pass3_commit_reason_payload(
        fc.RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
        pass3_committed=True,
        pass3_final_committed=True,
    )
    assert c is None and r is None


def test_partition_rejected_by_no_replacement_route_promoted_from_commit_field() -> None:
    c, r = partition_pass3_commit_reason_payload(
        fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE,
        pass3_committed=True,
        pass3_final_committed=True,
    )
    assert c is None
    assert r == fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE


def test_recovery_semantic_dto_namespaces_are_disjoint() -> None:
    """DTO namespace sets keep success commits separate from recovery/reject vocabulary."""

    assert fc.P3F_COMMIT_REASON_NORMAL_GAIN in COMMIT_REASON_VALUES
    assert fc.COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY in COMMIT_REASON_VALUES
    assert fc.RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK in RECOVERY_TRIGGER_VALUES
    assert fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE in INVALID_COMMIT_REASON_VALUES
    assert COMMIT_REASON_VALUES.isdisjoint(RECOVERY_TRIGGER_VALUES)
    assert COMMIT_REASON_VALUES.isdisjoint(INVALID_COMMIT_REASON_VALUES)


def test_recovery_semantic_dto_classifiers_match_contract() -> None:
    assert is_commit_reason(fc.P3F_COMMIT_REASON_NORMAL_GAIN)
    assert normalize_success_commit_reason(fc.P3F_COMMIT_REASON_NORMAL_GAIN) == "normal_gain"
    assert is_recovery_trigger(fc.RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK)
    assert not is_commit_reason(fc.RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK)
    assert is_invalid_commit_reason(fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE)
    assert (
        promote_misfiled_rejected_reason(fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE)
        == fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE
    )


def test_synthesize_post_reclaim_string_not_in_rollup_commit_reason() -> None:
    s = {
        "return_reason": "ok",
        "pass3_final_committed": True,
        "pass3_committed": True,
        "pass3_commit_reason": fc.RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    }
    synthesize_recovery_validation_outcome(s)
    assert s["recovery_validation_outcome"]["commit_reason"] is None


def test_synthesize_rejected_by_no_replacement_route_not_rollup_commit() -> None:
    s = {
        "return_reason": "ok",
        "pass3_final_committed": True,
        "pass3_committed": True,
        "pass3_commit_reason": fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE,
    }
    synthesize_recovery_validation_outcome(s)
    assert s["recovery_validation_outcome"]["commit_reason"] is None
