"""Track D — T2 throughput policy on diagnostic canon (observability only)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts import rttp_ops_policy as policy
from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    RTTP_DIAGNOSTIC_CANON_SLUG,
    RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON,
    RTTP_OPS_SLUG_CLASS_PASS_CAPABLE,
    RTTP_OPS_SLUG_CLASS_UNKNOWN,
    T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP,
    T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
    T2_POLICY_STATUS_SATISFIED,
    T2_POLICY_STATUS_SHORTFALL,
    T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON,
    classify_t2_policy,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import build_rttp_solver_summary


def test_diagnostic_canon_shortfall_is_expected() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=False,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
    assert row.t2_policy_reason == T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP
    assert row.diagnostic_expected_shortfall is True
    assert row.t3_ops_eligible is False
    assert row.t3_blocked_reason == T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON
    assert row.rttp_ops_slug_class == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON


def test_unknown_slug_shortfall_not_expected() -> None:
    row = classify_t2_policy(
        project_slug="some-other-slug",
        throughput_budget_satisfied=False,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_SHORTFALL
    assert row.t2_policy_reason is None
    assert row.diagnostic_expected_shortfall is False
    assert row.t3_ops_eligible is False
    assert row.t3_blocked_reason is None
    assert row.rttp_ops_slug_class == RTTP_OPS_SLUG_CLASS_UNKNOWN


def test_satisfied_on_any_slug() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=True,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_SATISFIED
    assert row.t2_policy_reason is None
    assert row.diagnostic_expected_shortfall is False
    assert row.t3_ops_eligible is True
    assert row.t3_blocked_reason is None


def test_no_policy_when_budget_none() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=None,
    )
    assert row.t2_policy_status is None
    assert row.as_summary_fields() == {}


def test_as_summary_fields_keys() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=False,
    )
    fields = row.as_summary_fields()
    assert fields["t2_policy_status"] == T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
    assert fields["diagnostic_expected_shortfall"] is True
    assert "throughput_budget_satisfied" not in fields


def test_build_rttp_solver_summary_omits_policy_without_throughput_budget_fields() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=1,
        commit_order=("a",),
        algorithm_steps=(),
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_fields=None,
    )
    assert "t2_policy_status" not in summary
    assert "diagnostic_expected_shortfall" not in summary


def test_pass_capable_slug_shortfall_never_expected(monkeypatch) -> None:
    monkeypatch.setattr(
        policy,
        "RTTP_PASS_CAPABLE_SLUGS",
        frozenset({"cert-reference-slug"}),
    )
    row = classify_t2_policy(
        project_slug="cert-reference-slug",
        throughput_budget_satisfied=False,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_SHORTFALL
    assert row.diagnostic_expected_shortfall is False
    assert row.rttp_ops_slug_class == RTTP_OPS_SLUG_CLASS_PASS_CAPABLE


def test_tiny_passable_v2_shortfall_never_expected_diagnostic() -> None:
    from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
        RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG,
        T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
    )

    row = classify_t2_policy(
        project_slug=RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG,
        throughput_budget_satisfied=False,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_SHORTFALL
    assert row.t2_policy_status != T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
    assert row.diagnostic_expected_shortfall is False


def test_build_rttp_solver_summary_merges_t2_policy_for_diagnostic_canon() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=32,
        normal_count=127,
        commit_order=("a",),
        algorithm_steps=(),
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_fields={
            "throughput_budget_satisfied": False,
            "throughput_target_percent": 10,
            "target_throughput_per_min": "7536.0000",
            "actual_committed_output_per_min": "3840.0000",
            "throughput_shortfall_per_min": "3696.0000",
            "reconstruction_max_throughput_per_min": "75360.0000",
        },
    )
    assert summary["validation_passed"] is True
    assert summary["throughput_budget_satisfied"] is False
    assert "throughput_target_shortfall" in summary["issue_codes"]
    assert summary["t2_policy_status"] == T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
    assert summary["diagnostic_expected_shortfall"] is True
    assert summary["t3_ops_eligible"] is False
