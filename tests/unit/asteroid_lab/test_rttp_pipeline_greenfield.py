"""RTTP greenfield pipeline golden — deterministic commit (G8 v0.1).

v0.1: identical ``PipelineResult`` on repeated runs.
v0.2 replay on/off parity: ``test_rttp_replay_on_off_parity`` in ``test_rttp_replay_parity.py``.
"""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def test_greenfield_pipeline_deterministic_commits_n_bundles(
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
    assert len(first.committed_throughput_factors) >= 1
    assert first.committed_throughput_factors == second.committed_throughput_factors


def test_pipeline_includes_deferred_retry_shadow_step_after_primary_commit(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value in step_ids
    shadow_idx = step_ids.index(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value)
    commit_idx = step_ids.index(RttpAlgorithmStepId.RTTP_COMMIT.value)
    assert shadow_idx < commit_idx
    shadow_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    assert shadow_row["passed"] is True
    assert shadow_row["metrics"]["source_phase"] == "primary_incremental_commit"
    assert shadow_row["metrics"]["observe_only"] is True
