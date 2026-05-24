"""Build persisted ``solver_summary`` payloads (output-only; never solver input)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.reconstruction.confidence import QUALITY_TIER_CONFIDENT
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.replay import event_types as et

RTTP_ALGORITHM_LABEL = "rttp_v0.1"


class RttpAlgorithmStepId(StrEnum):
    """Stable step ids inside ``solver_summary["algorithm_steps"]``."""

    RECONSTRUCTION = "reconstruction"
    RTTP_ROUTE_DOMAIN = "rttp.route_domain"
    RTTP_CANDIDATE_POOL = "rttp.candidate_pool"
    RTTP_GENOME_SELECTION = "rttp.genome_selection"
    RTTP_COMMIT = "rttp.commit"


def algorithm_step_summary_to_json(step: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one step row for JSON persistence."""

    row: dict[str, Any] = {
        "step_id": str(step["step_id"]),
        "phase": str(step["phase"]),
        "event_type": str(step["event_type"]),
        "title": str(step["title"]),
        "summary": str(step.get("summary") or ""),
        "metrics": dict(step.get("metrics") or {}),
    }
    passed = step.get("passed")
    if passed is not None:
        row["passed"] = bool(passed)
    return row


def reconstruction_step_from_result(recon: ReconstructionResult) -> dict[str, Any]:
    """Summarize reconstruction for ``solver_summary`` (read-only observability)."""

    summary_json = dict(recon.summary_json or {})
    metrics: dict[str, Any] = {
        "cell_count": len(recon.cells),
        "confidence_score": float(recon.confidence_score),
        "quality_tier": str(recon.quality_tier),
        "confirmed_cell_count": len(recon.confirmed_cells),
        "ambiguous_cell_count": len(recon.ambiguous_cells),
        "external_void_cell_count": len(recon.external_void_cells),
    }
    metrics.update(summary_json)
    tier = str(recon.quality_tier)
    lines = [
        "Map reconstruction complete.",
        f"quality_tier: {tier}",
        f"cell_count: {len(recon.cells)}",
        f"confidence_score: {recon.confidence_score:.3f}",
    ]
    return algorithm_step_summary_to_json(
        {
            "step_id": RttpAlgorithmStepId.RECONSTRUCTION.value,
            "phase": "reconstruction",
            "event_type": et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
            "title": "Map reconstruction",
            "summary": "\n".join(lines),
            "metrics": metrics,
            "passed": tier == QUALITY_TIER_CONFIDENT,
        }
    )


def extract_macro_commit_summary(
    algorithm_steps: Sequence[Mapping[str, Any]],
    *,
    macro_only_mode: bool,
    validation_passed: bool,
) -> dict[str, Any] | None:
    """Output-only macro commit HUD payload (never solver input)."""

    if not macro_only_mode:
        return None
    commit_metrics: dict[str, Any] = {}
    for step in algorithm_steps:
        if str(step.get("step_id")) == RttpAlgorithmStepId.RTTP_COMMIT.value:
            commit_metrics = dict(step.get("metrics") or {})
    return {
        "macro_only_mode": True,
        "committed_macro_ids": list(commit_metrics.get("committed_macro_ids") or []),
        "committed_child_ids": list(commit_metrics.get("committed_child_ids") or []),
        "domain_version": commit_metrics.get("domain_version"),
        "validation_passed": bool(validation_passed),
        "conflict_count": int(commit_metrics.get("conflict_count") or 0),
    }


def build_rttp_solver_summary(
    *,
    pipeline_ok: bool,
    committed_count: int,
    normal_count: int,
    commit_order: tuple[str, ...],
    algorithm_steps: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
    macro_only_mode: bool = False,
    reconstruction_step: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate RTTP scalars and per-step summaries for ``SolverRun.config_json``."""

    steps_json: list[dict[str, Any]] = []
    if reconstruction_step is not None:
        steps_json.append(algorithm_step_summary_to_json(reconstruction_step))
    steps_json.extend(algorithm_step_summary_to_json(step) for step in algorithm_steps)
    summary: dict[str, Any] = {
        "algorithm": RTTP_ALGORITHM_LABEL,
        "macro_only_mode": bool(macro_only_mode),
        "validation_passed": pipeline_ok,
        "run_success": pipeline_ok,
        "capacity_satisfied": pipeline_ok,
        "placement_capacity_satisfied": pipeline_ok,
        "throughput_budget_satisfied": pipeline_ok,
        "confirmed_count": committed_count,
        "target_miner_bundle_count": len(commit_order),
        "target_placement_count": len(commit_order),
        "normal_candidate_count": normal_count,
        "commit_order": list(commit_order),
        "issue_codes": [] if pipeline_ok else ["rttp_validation_failed"],
        "issue_details": [] if pipeline_ok else [],
        "algorithm_steps": steps_json,
    }
    macro_hud = extract_macro_commit_summary(
        algorithm_steps,
        macro_only_mode=macro_only_mode,
        validation_passed=pipeline_ok,
    )
    if macro_hud is not None:
        summary["macro_commit_summary"] = macro_hud
    return summary


__all__ = [
    "RTTP_ALGORITHM_LABEL",
    "RttpAlgorithmStepId",
    "algorithm_step_summary_to_json",
    "build_rttp_solver_summary",
    "extract_macro_commit_summary",
    "reconstruction_step_from_result",
]
