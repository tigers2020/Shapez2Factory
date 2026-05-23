"""RTTP greenfield pipeline golden — RTTP-G8 (PR-5)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline


def test_greenfield_pipeline_commits_n_bundles(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    first = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    second = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )

    assert first.normal_count >= 1
    assert len(first.commit_result.committed_ids) >= 1
    assert first.validation_passed
    assert first == second
    assert first.commit_result.committed_ids == second.commit_result.committed_ids
    assert first.genome.commit_order == second.genome.commit_order
