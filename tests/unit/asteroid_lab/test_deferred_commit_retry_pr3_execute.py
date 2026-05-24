"""PR-3 — bounded deferred commit retry execution."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.contracts.deferred_retry_execute import DeferredRetryExecuteResult
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import ExtractorPlacementPolicy
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import generate_candidates
from django_apps.asteroid_lab.optimization.commit.deferred_retry_execute import (
    merged_committed_ids_for_genome_order,
    run_bounded_deferred_retry,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitAttemptOutcome,
    CommitConflict,
    CommitConflictReason,
    CommitResult,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


def test_merged_committed_ids_follow_genome_order() -> None:
    """Recovered B between primary A and C must sort as (A, B, C)."""
    order = ("candidate_a", "candidate_b", "candidate_c")
    merged = merged_committed_ids_for_genome_order(
        commit_order=order,
        primary_committed_ids=("candidate_a", "candidate_c"),
        recovered_candidate_ids=("candidate_b",),
    )
    assert merged == ("candidate_a", "candidate_b", "candidate_c")


def test_deferred_retry_recovers_eligible_candidate_when_retry_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Executor merge path when retry attempt confirms (geometry-independent)."""
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    order = (first.candidate_id, second.candidate_id)
    pool = {first.candidate_id: first, second.candidate_id: second}
    primary = incremental_commit(
        PlacementGenome(commit_order=order),
        pool,
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    assert second.candidate_id not in primary.committed_ids

    def _retry_succeeds_for_second(
        candidate: object,
        **kwargs: object,
    ) -> CommitAttemptOutcome:
        bundle = candidate
        assert hasattr(bundle, "candidate_id")
        if bundle.candidate_id == second.candidate_id:
            return CommitAttemptOutcome(committed=True, route_cells=frozenset())
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                bundle.candidate_id,
                CommitConflictReason.REPROBE_FAILED,
            ),
        )

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.commit.deferred_retry_execute._attempt_commit_one",
        _retry_succeeds_for_second,
    )
    execute = run_bounded_deferred_retry(
        primary_commit_result=primary,
        commit_order=order,
        candidates_by_id=pool,
        inp=inp,
        skeleton=skeleton,
        config=DeferredRetryShadowConfig(enabled=True, observe_only=False),
    )
    merged = execute.merged_commit_result
    assert merged.committed_ids == order
    assert execute.recovered_candidate_ids == (second.candidate_id,)
    assert execute.deferred_retry_recovered_count == 1
    assert execute.deferred_retry_still_failed_count == 0
    assert not any(
        conflict.candidate_id == second.candidate_id
        and conflict.reason is CommitConflictReason.REPROBE_FAILED
        for conflict in merged.conflicts
    )


def test_deferred_retry_narrow_corridor_second_still_fails_after_retry() -> None:
    """B-CS1 geometry: second stays reprobe_failed; executor records still_failed."""
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    order = (first.candidate_id, second.candidate_id)
    pool = {first.candidate_id: first, second.candidate_id: second}
    primary = incremental_commit(
        PlacementGenome(commit_order=order),
        pool,
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    execute = run_bounded_deferred_retry(
        primary_commit_result=primary,
        commit_order=order,
        candidates_by_id=pool,
        inp=inp,
        skeleton=skeleton,
        config=DeferredRetryShadowConfig(enabled=True, observe_only=False),
    )
    assert execute.deferred_retry_attempted_count == 1
    assert execute.deferred_retry_recovered_count == 0
    assert execute.deferred_retry_still_failed_count == 1
    assert execute.recovered_candidate_ids == ()
    assert execute.deferred_retry_failed_reason_counts == {"reprobe_failed": 1}
    merged = execute.merged_commit_result
    reprobe_rows_for_second = [
        conflict
        for conflict in merged.conflicts
        if conflict.candidate_id == second.candidate_id
        and conflict.reason is CommitConflictReason.REPROBE_FAILED
    ]
    assert len(reprobe_rows_for_second) == 1


def test_deferred_retry_does_not_retry_inlet_or_overlap() -> None:
    primary = CommitResult(
        committed_ids=(),
        reserved_route_cells=frozenset(),
        domain_version=0,
        conflicts=(
            CommitConflict("x", CommitConflictReason.INLET_ON_SHARED_TRANSPORT),
            CommitConflict("y", CommitConflictReason.OVERLAP),
        ),
    )
    execute = run_bounded_deferred_retry(
        primary_commit_result=primary,
        commit_order=("x", "y"),
        candidates_by_id={},
        inp=build_narrow_corridor_optimization_input(),
        skeleton=RttpSkeletonBuilder.build(
            build_narrow_corridor_optimization_input(),
            config=RttpSkeletonConfig(),
        ),
        config=DeferredRetryShadowConfig(enabled=True, observe_only=False),
    )
    assert execute.merged_commit_result == primary
    assert execute.deferred_retry_recovered_count == 0


def test_deferred_retry_is_deterministic() -> None:
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    order = (first.candidate_id, second.candidate_id)
    pool = {first.candidate_id: first, second.candidate_id: second}
    primary = incremental_commit(
        PlacementGenome(commit_order=order),
        pool,
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    config = DeferredRetryShadowConfig(enabled=True, observe_only=False)
    first_run = run_bounded_deferred_retry(
        primary_commit_result=primary,
        commit_order=order,
        candidates_by_id=pool,
        inp=inp,
        skeleton=skeleton,
        config=config,
    )
    second_run = run_bounded_deferred_retry(
        primary_commit_result=primary,
        commit_order=order,
        candidates_by_id=pool,
        inp=inp,
        skeleton=skeleton,
        config=config,
    )
    assert first_run.merged_commit_result == second_run.merged_commit_result
    assert first_run.recovered_candidate_ids == second_run.recovered_candidate_ids


def test_disabled_shadow_does_not_append_execute_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(enabled=False),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value in step_ids
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value not in step_ids


def test_observe_only_true_does_not_append_execute_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(
                enabled=True,
                observe_only=True,
            ),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value not in step_ids


def test_observe_only_false_appends_execute_step_after_shadow(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        narrow_corridor_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(
                enabled=True,
                observe_only=False,
            ),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    shadow_idx = step_ids.index(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value)
    execute_idx = step_ids.index(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value)
    assert shadow_idx < execute_idx


def test_lns_receives_merged_not_primary_when_execution_ran(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    primary = CommitResult(
        committed_ids=("only_primary",),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict("retry_me", CommitConflictReason.REPROBE_FAILED),
            CommitConflict("stays", CommitConflictReason.OVERLAP),
        ),
    )
    merged = CommitResult(
        committed_ids=("only_primary", "retry_me"),
        reserved_route_cells=frozenset(),
        domain_version=2,
        conflicts=(CommitConflict("stays", CommitConflictReason.OVERLAP),),
    )
    execute_stub = DeferredRetryExecuteResult(
        merged_commit_result=merged,
        deferred_retry_rounds_executed=1,
        deferred_retry_eligible_count=1,
        deferred_retry_attempted_count=1,
        deferred_retry_recovered_count=1,
        deferred_retry_still_failed_count=0,
        recovered_candidate_ids=("retry_me",),
        deferred_retry_failed_reason_counts={},
    )
    seen_lns: list[CommitResult] = []

    def _fake_incremental_commit(*_args: object, **_kwargs: object) -> CommitResult:
        return primary

    def _fake_execute(**_kwargs: object) -> DeferredRetryExecuteResult:
        return execute_stub

    def _capture_lns(*args: object, **_kwargs: object) -> tuple[object, object]:
        seen_lns.append(args[4])
        return args[2], args[4]

    with (
        patch(
            "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
            side_effect=_fake_incremental_commit,
        ),
        patch(
            "django_apps.asteroid_lab.optimization.pipeline.run_bounded_deferred_retry",
            side_effect=_fake_execute,
        ),
        patch(
            "django_apps.asteroid_lab.optimization.pipeline.run_local_lns",
            side_effect=_capture_lns,
        ),
    ):
        run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            pipeline_config=RttpPipelineConfig(
                deferred_retry_shadow=DeferredRetryShadowConfig(
                    enabled=True,
                    observe_only=False,
                ),
            ),
        )
    assert seen_lns
    assert seen_lns[0] is merged
    assert seen_lns[0] is not primary
    assert seen_lns[0].committed_ids == ("only_primary", "retry_me")
