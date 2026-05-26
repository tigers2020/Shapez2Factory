"""RTTP ops authority tokens (T2 policy); not solver algorithm input."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RTTP_DIAGNOSTIC_CANON_SLUG = "copy-import-495e552c"

T2_POLICY_STATUS_SATISFIED = "satisfied"
T2_POLICY_STATUS_SHORTFALL = "shortfall"
T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL = "expected_diagnostic_shortfall"

T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP = "diagnostic_canon_route_feasible_gap"

T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON = (
    "t2_not_pass_capable_on_diagnostic_canon"
)

RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON = "diagnostic_canon"
RTTP_OPS_SLUG_CLASS_UNKNOWN = "unknown"

ALL_T2_POLICY_STATUSES: frozenset[str] = frozenset(
    {
        T2_POLICY_STATUS_SATISFIED,
        T2_POLICY_STATUS_SHORTFALL,
        T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
    }
)


def is_diagnostic_canon_slug(project_slug: str | None) -> bool:
    if not project_slug:
        return False
    return project_slug.strip() == RTTP_DIAGNOSTIC_CANON_SLUG


@dataclass(frozen=True, slots=True)
class T2PolicyClassification:
    t2_policy_status: str | None
    t2_policy_reason: str | None
    diagnostic_expected_shortfall: bool
    t3_ops_eligible: bool
    t3_blocked_reason: str | None
    rttp_ops_slug_class: str

    def as_summary_fields(self) -> dict[str, Any]:
        if self.t2_policy_status is None:
            return {}
        out: dict[str, Any] = {
            "t2_policy_status": self.t2_policy_status,
            "diagnostic_expected_shortfall": self.diagnostic_expected_shortfall,
            "t3_ops_eligible": self.t3_ops_eligible,
            "rttp_ops_slug_class": self.rttp_ops_slug_class,
        }
        if self.t2_policy_reason is not None:
            out["t2_policy_reason"] = self.t2_policy_reason
        if self.t3_blocked_reason is not None:
            out["t3_blocked_reason"] = self.t3_blocked_reason
        return out


def classify_t2_policy(
    *,
    project_slug: str | None,
    throughput_budget_satisfied: bool | None,
) -> T2PolicyClassification:
    if throughput_budget_satisfied is None:
        return T2PolicyClassification(
            t2_policy_status=None,
            t2_policy_reason=None,
            diagnostic_expected_shortfall=False,
            t3_ops_eligible=False,
            t3_blocked_reason=None,
            rttp_ops_slug_class=RTTP_OPS_SLUG_CLASS_UNKNOWN,
        )

    slug_class = (
        RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON
        if is_diagnostic_canon_slug(project_slug)
        else RTTP_OPS_SLUG_CLASS_UNKNOWN
    )

    if throughput_budget_satisfied:
        return T2PolicyClassification(
            t2_policy_status=T2_POLICY_STATUS_SATISFIED,
            t2_policy_reason=None,
            diagnostic_expected_shortfall=False,
            t3_ops_eligible=True,
            t3_blocked_reason=None,
            rttp_ops_slug_class=slug_class,
        )

    if is_diagnostic_canon_slug(project_slug):
        return T2PolicyClassification(
            t2_policy_status=T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
            t2_policy_reason=T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP,
            diagnostic_expected_shortfall=True,
            t3_ops_eligible=False,
            t3_blocked_reason=T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON,
            rttp_ops_slug_class=RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON,
        )

    return T2PolicyClassification(
        t2_policy_status=T2_POLICY_STATUS_SHORTFALL,
        t2_policy_reason=None,
        diagnostic_expected_shortfall=False,
        t3_ops_eligible=False,
        t3_blocked_reason=None,
        rttp_ops_slug_class=slug_class,
    )


__all__ = [
    "ALL_T2_POLICY_STATUSES",
    "RTTP_DIAGNOSTIC_CANON_SLUG",
    "T2PolicyClassification",
    "T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP",
    "T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL",
    "T2_POLICY_STATUS_SATISFIED",
    "T2_POLICY_STATUS_SHORTFALL",
    "T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON",
    "RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON",
    "RTTP_OPS_SLUG_CLASS_UNKNOWN",
    "classify_t2_policy",
    "is_diagnostic_canon_slug",
]
