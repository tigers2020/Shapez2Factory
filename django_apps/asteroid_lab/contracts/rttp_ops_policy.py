"""RTTP ops tokens (T2 policy, slug class, T3 certification); not solver algorithm input."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

RTTP_DIAGNOSTIC_CANON_SLUG = "copy-import-495e552c"

RTTP_DIAGNOSTIC_CANON_SLUGS: frozenset[str] = frozenset({RTTP_DIAGNOSTIC_CANON_SLUG})

# Track B Task 4 (2026-05-30): borderline T2 pass (actual=target=480); fixture slug is SoT.
RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG = "rttp-cert-candidate-tiny-passable-v2"

RTTP_PASS_CAPABLE_SLUGS: frozenset[str] = frozenset(
    {RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG},
)

T2_POLICY_STATUS_SATISFIED = "satisfied"
T2_POLICY_STATUS_SHORTFALL = "shortfall"
T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL = "expected_diagnostic_shortfall"

T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP = "diagnostic_canon_route_feasible_gap"

T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON = (
    "t2_not_pass_capable_on_diagnostic_canon"
)

RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON = "diagnostic_canon"
RTTP_OPS_SLUG_CLASS_PASS_CAPABLE = "pass_capable"
RTTP_OPS_SLUG_CLASS_UNKNOWN = "unknown"

ALL_RTTP_OPS_SLUG_CLASSES: frozenset[str] = frozenset(
    {
        RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON,
        RTTP_OPS_SLUG_CLASS_PASS_CAPABLE,
        RTTP_OPS_SLUG_CLASS_UNKNOWN,
    }
)

ALL_T2_POLICY_STATUSES: frozenset[str] = frozenset(
    {
        T2_POLICY_STATUS_SATISFIED,
        T2_POLICY_STATUS_SHORTFALL,
        T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
    }
)

CERT_STATUS_CERTIFIED_PASS = "certified_pass"
CERT_STATUS_FAIL_T1B = "fail_t1b"
CERT_STATUS_FAIL_T2 = "fail_t2"
CERT_STATUS_FAIL_T3_SHELL = "fail_t3_shell"
CERT_STATUS_FAIL_RUNTIME = "fail_runtime"
CERT_STATUS_SKIPPED_DIAGNOSTIC = "skipped_diagnostic"
CERT_STATUS_SKIPPED_NO_MAP = "skipped_no_map"

ALL_CERT_STATUSES: frozenset[str] = frozenset(
    {
        CERT_STATUS_CERTIFIED_PASS,
        CERT_STATUS_FAIL_T1B,
        CERT_STATUS_FAIL_T2,
        CERT_STATUS_FAIL_T3_SHELL,
        CERT_STATUS_FAIL_RUNTIME,
        CERT_STATUS_SKIPPED_DIAGNOSTIC,
        CERT_STATUS_SKIPPED_NO_MAP,
    }
)

ISSUE_CODE_THROUGHPUT_TARGET_SHORTFALL = "throughput_target_shortfall"
RTTP_COMMIT_STEP_ID = "rttp.commit"
RTTP_GENOME_SELECTION_STEP_ID = "rttp.genome_selection"


def is_diagnostic_canon_slug(project_slug: str | None) -> bool:
    if not project_slug:
        return False
    return project_slug.strip() in RTTP_DIAGNOSTIC_CANON_SLUGS


def classify_rttp_ops_slug(project_slug: str | None) -> str:
    """Resolve slug class; diagnostic canon wins over pass_capable if misconfigured."""
    if not project_slug:
        return RTTP_OPS_SLUG_CLASS_UNKNOWN
    normalized = project_slug.strip()
    if normalized in RTTP_DIAGNOSTIC_CANON_SLUGS:
        return RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON
    if normalized in RTTP_PASS_CAPABLE_SLUGS:
        return RTTP_OPS_SLUG_CLASS_PASS_CAPABLE
    return RTTP_OPS_SLUG_CLASS_UNKNOWN


def t2_policy_status_for_slug_class(
    *,
    slug_class: str,
    throughput_budget_satisfied: bool | None,
) -> str | None:
    if throughput_budget_satisfied is None:
        return None
    if throughput_budget_satisfied:
        return T2_POLICY_STATUS_SATISFIED
    if slug_class == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON:
        return T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
    return T2_POLICY_STATUS_SHORTFALL


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
    slug_class = classify_rttp_ops_slug(project_slug)
    status = t2_policy_status_for_slug_class(
        slug_class=slug_class,
        throughput_budget_satisfied=throughput_budget_satisfied,
    )
    if status is None:
        return T2PolicyClassification(
            t2_policy_status=None,
            t2_policy_reason=None,
            diagnostic_expected_shortfall=False,
            t3_ops_eligible=False,
            t3_blocked_reason=None,
            rttp_ops_slug_class=slug_class,
        )

    if status == T2_POLICY_STATUS_SATISFIED:
        return T2PolicyClassification(
            t2_policy_status=status,
            t2_policy_reason=None,
            diagnostic_expected_shortfall=False,
            t3_ops_eligible=True,
            t3_blocked_reason=None,
            rttp_ops_slug_class=slug_class,
        )

    if status == T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL:
        return T2PolicyClassification(
            t2_policy_status=status,
            t2_policy_reason=T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP,
            diagnostic_expected_shortfall=True,
            t3_ops_eligible=False,
            t3_blocked_reason=T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON,
            rttp_ops_slug_class=slug_class,
        )

    return T2PolicyClassification(
        t2_policy_status=T2_POLICY_STATUS_SHORTFALL,
        t2_policy_reason=None,
        diagnostic_expected_shortfall=False,
        t3_ops_eligible=False,
        t3_blocked_reason=None,
        rttp_ops_slug_class=slug_class,
    )


def _pipeline_step_by_id(
    pipeline_steps: Sequence[Mapping[str, Any]],
    step_id: str,
) -> Mapping[str, Any] | None:
    for step in pipeline_steps:
        if str(step.get("step_id")) == step_id:
            return step
    return None


def _issue_codes_list(solver_summary: Mapping[str, Any]) -> list[str]:
    raw = solver_summary.get("issue_codes")
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(code) for code in raw]
    return [str(raw)]


@dataclass(frozen=True, slots=True)
class T3CertificationResult:
    cert_status: str
    slug_class: str
    t0_pass: bool
    t1a_pass: bool
    t1b_pass: bool
    t2_pass: bool
    t3_shell_pass: bool


def evaluate_t3_certification(
    *,
    slug: str,
    solver_summary: Mapping[str, Any],
    pipeline_steps: Sequence[Mapping[str, Any]],
) -> T3CertificationResult:
    """Read-only T3 tier evaluation over persisted summary and pipeline steps."""
    slug_class = classify_rttp_ops_slug(slug)
    if slug_class == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON:
        return T3CertificationResult(
            cert_status=CERT_STATUS_SKIPPED_DIAGNOSTIC,
            slug_class=slug_class,
            t0_pass=False,
            t1a_pass=False,
            t1b_pass=False,
            t2_pass=False,
            t3_shell_pass=False,
        )

    commit_step = _pipeline_step_by_id(pipeline_steps, RTTP_COMMIT_STEP_ID)
    selection_step = _pipeline_step_by_id(pipeline_steps, RTTP_GENOME_SELECTION_STEP_ID)

    confirmed_count = int(solver_summary.get("confirmed_count") or 0)
    t1a_pass = commit_step is not None and confirmed_count > 0

    t1b_pass = False
    if commit_step is not None:
        t1b_pass = bool(commit_step.get("passed"))
        metrics = commit_step.get("metrics")
        if isinstance(metrics, Mapping) and "validation_passed" in metrics:
            t1b_pass = bool(metrics.get("validation_passed"))

    issue_codes = _issue_codes_list(solver_summary)
    throughput_ok = solver_summary.get("throughput_budget_satisfied") is True
    t2_pass = throughput_ok and ISSUE_CODE_THROUGHPUT_TARGET_SHORTFALL not in issue_codes

    validation_passed = solver_summary.get("validation_passed") is True
    t3_shell_pass = validation_passed and issue_codes == []

    t0_pass = selection_step is not None

    if t0_pass and t1a_pass and t1b_pass and t2_pass and t3_shell_pass:
        cert_status = CERT_STATUS_CERTIFIED_PASS
    elif not t1a_pass or not t1b_pass:
        cert_status = CERT_STATUS_FAIL_T1B
    elif not t2_pass:
        cert_status = CERT_STATUS_FAIL_T2
    elif not t3_shell_pass or not t0_pass:
        cert_status = CERT_STATUS_FAIL_T3_SHELL
    else:
        cert_status = CERT_STATUS_FAIL_RUNTIME

    return T3CertificationResult(
        cert_status=cert_status,
        slug_class=slug_class,
        t0_pass=t0_pass,
        t1a_pass=t1a_pass,
        t1b_pass=t1b_pass,
        t2_pass=t2_pass,
        t3_shell_pass=t3_shell_pass,
    )


__all__ = [
    "ALL_CERT_STATUSES",
    "ALL_RTTP_OPS_SLUG_CLASSES",
    "ALL_T2_POLICY_STATUSES",
    "CERT_STATUS_CERTIFIED_PASS",
    "CERT_STATUS_FAIL_RUNTIME",
    "CERT_STATUS_FAIL_T1B",
    "CERT_STATUS_FAIL_T2",
    "CERT_STATUS_FAIL_T3_SHELL",
    "CERT_STATUS_SKIPPED_DIAGNOSTIC",
    "CERT_STATUS_SKIPPED_NO_MAP",
    "ISSUE_CODE_THROUGHPUT_TARGET_SHORTFALL",
    "RTTP_COMMIT_STEP_ID",
    "RTTP_DIAGNOSTIC_CANON_SLUG",
    "RTTP_DIAGNOSTIC_CANON_SLUGS",
    "RTTP_GENOME_SELECTION_STEP_ID",
    "RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON",
    "RTTP_OPS_SLUG_CLASS_PASS_CAPABLE",
    "RTTP_OPS_SLUG_CLASS_UNKNOWN",
    "RTTP_PASS_CAPABLE_SLUGS",
    "RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG",
    "T2PolicyClassification",
    "T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP",
    "T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL",
    "T2_POLICY_STATUS_SATISFIED",
    "T2_POLICY_STATUS_SHORTFALL",
    "T3CertificationResult",
    "T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON",
    "classify_rttp_ops_slug",
    "classify_t2_policy",
    "evaluate_t3_certification",
    "is_diagnostic_canon_slug",
    "t2_policy_status_for_slug_class",
]
