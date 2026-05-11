"""§13 recovery context: trigger vs commit vs rollback semantics (solver summary / trace).

Chain segments are append-only stage markers for post–Pass3 orchestration (P4 reclaim,
soft replace, post-reclaim Pass3). See project step docs §13.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_SEGMENT_P4_RECLAIM,
    RECOVERY_SEGMENT_POST_RECLAIM_PASS3,
    RECOVERY_SEGMENT_SOFT_REPLACE_V2,
    RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    sync_recovery_total_attempts_used_from_chain,
)

__all__ = [
    "RECOVERY_SEGMENT_P4_RECLAIM",
    "RECOVERY_SEGMENT_POST_RECLAIM_PASS3",
    "RECOVERY_SEGMENT_SOFT_REPLACE_V2",
    "RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM",
    "extend_recovery_chain",
    "finalize_recovery_terminal_reason",
]


def extend_recovery_chain(target: dict[str, Any], segment: str) -> None:
    """Append ``segment`` to ``target[\"recovery_context_chain\"]`` if not already last.

    Avoids duplicate consecutive tags from inner loops; keeps prior segments intact.
    """

    chain = target.get("recovery_context_chain")
    if not isinstance(chain, list):
        chain = []
        target["recovery_context_chain"] = chain
    if chain and chain[-1] == segment:
        return
    chain.append(segment)


def finalize_recovery_terminal_reason(pass3_summary: dict[str, Any]) -> None:
    """Set ``recovery_terminal_reason`` from orchestration outcome (§13).

    Kept separate from per-commit ``rollback_reason`` fields on the summary.
    """

    if not pass3_summary.get("recovery_trigger_reason"):
        pass3_summary["recovery_terminal_reason"] = None
        sync_recovery_total_attempts_used_from_chain(pass3_summary)
        return
    if pass3_summary.get("post_reclaim_pass3_map_accepted"):
        pass3_summary["recovery_terminal_reason"] = "post_reclaim_pass3_success"
        sync_recovery_total_attempts_used_from_chain(pass3_summary)
        return
    pr_skip = pass3_summary.get("post_reclaim_pass3_skip_reason")
    if pr_skip is not None and str(pr_skip):
        pass3_summary["recovery_terminal_reason"] = str(pr_skip)
        sync_recovery_total_attempts_used_from_chain(pass3_summary)
        return
    if pass3_summary.get("post_reclaim_pass3_pass3_reverted"):
        pass3_summary["recovery_terminal_reason"] = (
            "final_validation_failed_after_post_reclaim_pass3"
        )
        sync_recovery_total_attempts_used_from_chain(pass3_summary)
        return
    pass3_summary["recovery_terminal_reason"] = str(
        pass3_summary.get("p4_reclaim_loop_terminated_reason") or "p4_reclaim_complete"
    )
    sync_recovery_total_attempts_used_from_chain(pass3_summary)
