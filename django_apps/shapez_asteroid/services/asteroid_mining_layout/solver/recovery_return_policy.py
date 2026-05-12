"""Algorithm §4.3 / §13 recovery **return policy** (spec table only; D2-B/C wire-up).

Canonical trigger strings live in ``foundation.constants``. The orchestrator calls
:func:`recovery_return_policy_for_trigger` for ``step4_routing_failure`` before at most one
remedial ``run_step4_stage``; other triggers remain table-only until wired.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE,
    RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
    RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE,
    RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
)

__all__ = [
    "RecoveryReturnPolicy",
    "RecoveryReturnPolicyId",
    "recovery_return_policy_for_trigger",
    "recovery_return_policy_triggers",
]


class RecoveryReturnPolicyId(StrEnum):
    """Stable id for §4.3 return-path summary (tests snapshot this)."""

    STEP4_RETRY_ROLLBACK_ALTERNATE_TRUNK = "STEP4_RETRY_ROLLBACK_ALTERNATE_TRUNK"
    STEP4_RETRY_TRUNK_SPLIT_OFFENDING_ROLLBACK = "STEP4_RETRY_TRUNK_SPLIT_OFFENDING_ROLLBACK"
    ROLLBACK_PASS3_THEN_STEP6_RECLAIM = "ROLLBACK_PASS3_THEN_STEP6_RECLAIM"
    ROLLBACK_RERUN_THEN_STEP9_NO_EXTRA_RERUN = "ROLLBACK_RERUN_THEN_STEP9_NO_EXTRA_RERUN"
    ROLLBACK_CANDIDATE_CONTINUE_STEP6 = "ROLLBACK_CANDIDATE_CONTINUE_STEP6"
    STEP9_REVALIDATE_ONLY_BOUNDED = "STEP9_REVALIDATE_ONLY_BOUNDED"


@dataclass(frozen=True, slots=True)
class RecoveryReturnPolicy:
    """Per-trigger return contract aligned with Algorithm ``02`` §4.3 / §4.3.1 / §4.3.2."""

    policy_id: RecoveryReturnPolicyId
    reenters_step4: bool
    allows_extra_post_reclaim_pass3_rerun: bool
    allows_one_time_remedial_step4: bool
    primary_return_steps: tuple[str, ...]


def recovery_return_policy_for_trigger(trigger: str) -> RecoveryReturnPolicy:
    """Return the §4.3 policy row for ``trigger`` (exact id string from constants)."""

    row = _POLICY_TABLE.get(trigger)
    if row is None:
        raise ValueError(f"unknown recovery trigger for policy table: {trigger!r}")
    return row


def recovery_return_policy_triggers() -> frozenset[str]:
    """Trigger ids that have an Algorithm §4.3 return-policy row (regression guard)."""

    return frozenset(_POLICY_TABLE)


_POLICY_TABLE: Final[dict[str, RecoveryReturnPolicy]] = {
    # §4.3: STEP4 route failure → retry / rollback / alternate trunk.
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE: RecoveryReturnPolicy(
        policy_id=RecoveryReturnPolicyId.STEP4_RETRY_ROLLBACK_ALTERNATE_TRUNK,
        reenters_step4=True,
        allows_extra_post_reclaim_pass3_rerun=False,
        allows_one_time_remedial_step4=False,
        primary_return_steps=("STEP4",),
    ),
    # §4.3: capacity split / trunk failure → STEP4 retry; trunk split / offending rollback.
    RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE: RecoveryReturnPolicy(
        policy_id=RecoveryReturnPolicyId.STEP4_RETRY_TRUNK_SPLIT_OFFENDING_ROLLBACK,
        reenters_step4=True,
        allows_extra_post_reclaim_pass3_rerun=False,
        allows_one_time_remedial_step4=False,
        primary_return_steps=("STEP4",),
    ),
    # §4.3 + §4.3.1: rollback Pass3 → STEP6 reclaim; optional bounded remedial STEP4 path.
    RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK: RecoveryReturnPolicy(
        policy_id=RecoveryReturnPolicyId.ROLLBACK_PASS3_THEN_STEP6_RECLAIM,
        reenters_step4=False,
        allows_extra_post_reclaim_pass3_rerun=False,
        allows_one_time_remedial_step4=True,
        primary_return_steps=("Pass3", "STEP6"),
    ),
    # §4.3.2: rerun rollback → STEP9; no additional post-reclaim Pass3 rerun in the same block.
    RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK: RecoveryReturnPolicy(
        policy_id=RecoveryReturnPolicyId.ROLLBACK_RERUN_THEN_STEP9_NO_EXTRA_RERUN,
        reenters_step4=False,
        allows_extra_post_reclaim_pass3_rerun=False,
        allows_one_time_remedial_step4=False,
        primary_return_steps=("STEP9",),
    ),
    # §4.3: incremental reclaim rollback → continue STEP6 reclaim loop.
    RECOVERY_TRIGGER_RECLAIM_INCREMENTAL_FAILURE: RecoveryReturnPolicy(
        policy_id=RecoveryReturnPolicyId.ROLLBACK_CANDIDATE_CONTINUE_STEP6,
        reenters_step4=False,
        allows_extra_post_reclaim_pass3_rerun=False,
        allows_one_time_remedial_step4=False,
        primary_return_steps=("STEP6",),
    ),
    # §4.3 + ``13_step9_validation`` §15: bounded validation recovery → STEP9 revalidation;
    # no automatic STEP4 re-entry (Pass3→P4→finalize loop may repeat without STEP4).
    RECOVERY_TRIGGER_FINAL_VALIDATION_FAILURE: RecoveryReturnPolicy(
        policy_id=RecoveryReturnPolicyId.STEP9_REVALIDATE_ONLY_BOUNDED,
        reenters_step4=False,
        allows_extra_post_reclaim_pass3_rerun=False,
        allows_one_time_remedial_step4=False,
        primary_return_steps=("Pass3", "P4", "STEP9"),
    ),
}
