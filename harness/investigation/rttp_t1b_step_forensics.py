"""Parse algorithm_steps for T1b investigation forensics (E.2 / E.3)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def _step_metrics(steps: Sequence[Mapping[str, object]], step_id: str) -> Mapping[str, object]:
    for step in steps:
        if str(step.get("step_id")) == step_id:
            metrics = step.get("metrics")
            if isinstance(metrics, Mapping):
                return metrics
    return {}


def _committed_count(commit_metrics: Mapping[str, object]) -> int:
    committed_ids = commit_metrics.get("committed_ids")
    if isinstance(committed_ids, Sequence) and not isinstance(committed_ids, str):
        return len(committed_ids)
    return 0


def extract_t1b_forensics(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    commit_metrics = _step_metrics(algorithm_steps, RttpAlgorithmStepId.RTTP_COMMIT.value)
    catalog_metrics = _step_metrics(
        algorithm_steps,
        RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value,
    )

    commit_step = next(
        (
            step
            for step in algorithm_steps
            if str(step.get("step_id")) == RttpAlgorithmStepId.RTTP_COMMIT.value
        ),
        None,
    )
    catalog_step = next(
        (
            step
            for step in algorithm_steps
            if str(step.get("step_id"))
            == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
        ),
        None,
    )

    commit_passed = bool(commit_step.get("passed")) if commit_step else None
    validation_passed = commit_metrics.get("validation_passed")
    catalog_passed = bool(catalog_step.get("passed")) if catalog_step else None

    mismatch_raw = catalog_metrics.get("mismatch_candidate_count")
    catalog_mismatch_count = int(mismatch_raw) if isinstance(mismatch_raw, int) else None

    pipeline_composition_anomaly = (
        commit_passed is not None
        and validation_passed is not None
        and commit_passed != validation_passed
    )

    return {
        "commit_passed": commit_passed,
        "validation_passed": validation_passed,
        "committed_count": _committed_count(commit_metrics),
        "conflict_count": commit_metrics.get("conflict_count"),
        "catalog_passed": catalog_passed,
        "catalog_mismatch_count": catalog_mismatch_count,
        "catalog_error_issue_codes": catalog_metrics.get("catalog_error_issue_codes"),
        "pipeline_composition_anomaly": pipeline_composition_anomaly,
    }


__all__ = ["extract_t1b_forensics"]
