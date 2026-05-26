"""Track B — T3 certification evaluator (read-only summary + pipeline steps)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    CERT_STATUS_CERTIFIED_PASS,
    CERT_STATUS_FAIL_T1B,
    CERT_STATUS_FAIL_T2,
    CERT_STATUS_FAIL_T3_SHELL,
    CERT_STATUS_SKIPPED_DIAGNOSTIC,
    RTTP_DIAGNOSTIC_CANON_SLUG,
    RTTP_OPS_SLUG_CLASS_PASS_CAPABLE,
    RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG,
    evaluate_t3_certification,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def _commit_step(*, passed: bool = True) -> dict[str, object]:
    return {
        "step_id": RttpAlgorithmStepId.RTTP_COMMIT.value,
        "passed": passed,
        "metrics": {"validation_passed": passed, "committed_ids": ["c1"]},
    }


def _selection_step() -> dict[str, object]:
    return {
        "step_id": RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value,
        "passed": True,
        "metrics": {"selection_mode": "greedy"},
    }


def test_pipeline_step_ids_match_policy_constants() -> None:
    from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
        RTTP_COMMIT_STEP_ID,
        RTTP_GENOME_SELECTION_STEP_ID,
        _pipeline_step_by_id,
    )

    steps = (_selection_step(), _commit_step(passed=True))
    assert _pipeline_step_by_id(steps, RTTP_GENOME_SELECTION_STEP_ID) is not None
    assert _pipeline_step_by_id(steps, RTTP_COMMIT_STEP_ID) is not None


def test_tiny_passable_v2_borderline_certified_pass_evidence() -> None:
    """Task 4 evidence shape: actual_committed=480 == target_80=480 (solver_run_id 151)."""
    summary = {
        "validation_passed": True,
        "issue_codes": [],
        "confirmed_count": 4,
        "throughput_budget_satisfied": True,
        "actual_committed_output_per_min": "480.0000",
        "target_throughput_per_min": "480.0000",
    }
    steps = (
        _selection_step(),
        {
            "step_id": RttpAlgorithmStepId.RTTP_COMMIT.value,
            "passed": True,
            "metrics": {
                "validation_passed": True,
                "committed_ids": [
                    "-1,9:cat_canon_manual_Layout_ShapeMiner_N:shape_belt",
                    "-2,8:cat_canon_manual_Layout_ShapeMiner_E:shape_belt",
                    "-1,10:cat_canon_manual_Layout_ShapeMiner_S:shape_belt",
                    "-1,8:cat_canon_manual_Layout_ShapeMiner_W:shape_belt",
                ],
            },
        },
    )
    result = evaluate_t3_certification(
        slug=RTTP_PASS_CAPABLE_TINY_PASSABLE_V2_SLUG,
        solver_summary=summary,
        pipeline_steps=steps,
    )
    assert result.slug_class == RTTP_OPS_SLUG_CLASS_PASS_CAPABLE
    assert result.cert_status == CERT_STATUS_CERTIFIED_PASS
    assert result.t1b_pass is True
    assert result.t2_pass is True
    assert result.t3_shell_pass is True


def test_certified_pass_when_all_tiers_satisfied() -> None:
    summary = {
        "validation_passed": True,
        "issue_codes": [],
        "confirmed_count": 1,
        "throughput_budget_satisfied": True,
    }
    steps = (_selection_step(), _commit_step(passed=True))
    result = evaluate_t3_certification(
        slug="cert-candidate-slug",
        solver_summary=summary,
        pipeline_steps=steps,
    )
    assert result.cert_status == CERT_STATUS_CERTIFIED_PASS
    assert result.t0_pass is True
    assert result.t1a_pass is True
    assert result.t1b_pass is True
    assert result.t2_pass is True
    assert result.t3_shell_pass is True


def test_skipped_diagnostic_for_canon_slug() -> None:
    result = evaluate_t3_certification(
        slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        solver_summary={"validation_passed": False, "issue_codes": ["x"]},
        pipeline_steps=(),
    )
    assert result.cert_status == CERT_STATUS_SKIPPED_DIAGNOSTIC


def test_fail_t1b_when_commit_not_passed() -> None:
    summary = {
        "validation_passed": False,
        "issue_codes": ["rttp_validation_failed"],
        "confirmed_count": 1,
        "throughput_budget_satisfied": True,
    }
    steps = (_selection_step(), _commit_step(passed=False))
    result = evaluate_t3_certification(
        slug="other-slug",
        solver_summary=summary,
        pipeline_steps=steps,
    )
    assert result.cert_status == CERT_STATUS_FAIL_T1B
    assert result.t1b_pass is False


def test_fail_t2_when_throughput_budget_unsatisfied() -> None:
    summary = {
        "validation_passed": True,
        "issue_codes": ["throughput_target_shortfall"],
        "confirmed_count": 2,
        "throughput_budget_satisfied": False,
    }
    steps = (_selection_step(), _commit_step(passed=True))
    result = evaluate_t3_certification(
        slug="other-slug",
        solver_summary=summary,
        pipeline_steps=steps,
    )
    assert result.cert_status == CERT_STATUS_FAIL_T2
    assert result.t2_pass is False


def test_fail_t3_shell_when_validation_not_passed() -> None:
    summary = {
        "validation_passed": False,
        "issue_codes": [],
        "confirmed_count": 1,
        "throughput_budget_satisfied": True,
    }
    steps = (_selection_step(), _commit_step(passed=True))
    result = evaluate_t3_certification(
        slug="other-slug",
        solver_summary=summary,
        pipeline_steps=steps,
    )
    assert result.cert_status == CERT_STATUS_FAIL_T3_SHELL
    assert result.t3_shell_pass is False


def test_fail_t3_shell_when_issue_codes_non_empty() -> None:
    summary = {
        "validation_passed": True,
        "issue_codes": ["unexpected_issue"],
        "confirmed_count": 1,
        "throughput_budget_satisfied": True,
    }
    steps = (_selection_step(), _commit_step(passed=True))
    result = evaluate_t3_certification(
        slug="other-slug",
        solver_summary=summary,
        pipeline_steps=steps,
    )
    assert result.cert_status == CERT_STATUS_FAIL_T3_SHELL


def test_fail_t3_shell_when_selection_step_missing() -> None:
    summary = {
        "validation_passed": True,
        "issue_codes": [],
        "confirmed_count": 1,
        "throughput_budget_satisfied": True,
    }
    result = evaluate_t3_certification(
        slug="other-slug",
        solver_summary=summary,
        pipeline_steps=(_commit_step(passed=True),),
    )
    assert result.t0_pass is False
    assert result.cert_status == CERT_STATUS_FAIL_T3_SHELL
