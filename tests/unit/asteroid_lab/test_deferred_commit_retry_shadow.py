"""PR-1 deferred commit retry shadow — observe-only contracts."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.contracts.deferred_retry_shadow import (
    PRIMARY_INCREMENTAL_COMMIT_PHASE,
    DeferredRetryShadowConfig,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.deferred_retry_shadow import (
    build_deferred_retry_shadow_summary,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SHADOW_MODULE = (
    _REPO_ROOT / "django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py"
)


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


def test_deferred_retry_shadow_contract_imports() -> None:
    from django_apps.asteroid_lab.contracts.deferred_retry_shadow import (
        DeferredRetryShadowBudget,
        DeferredRetryShadowCandidate,
        DeferredRetryShadowConfig,
        DeferredRetryShadowSummary,
    )

    assert PRIMARY_INCREMENTAL_COMMIT_PHASE == "primary_incremental_commit"
    assert DeferredRetryShadowConfig().enabled is True
    assert DeferredRetryShadowSummary.__dataclass_fields__
    assert DeferredRetryShadowCandidate.__dataclass_fields__
    assert DeferredRetryShadowBudget.__dataclass_fields__


def test_deferred_shadow_records_reprobe_failed_after_primary_commit(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    genome = PlacementGenome(
        commit_order=(first.candidate_id, second.candidate_id),
    )
    candidates_by_id = {
        first.candidate_id: first,
        second.candidate_id: second,
    }
    domain = initial_commit_domain(skeleton, inp)
    primary = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    shadow = build_deferred_retry_shadow_summary(
        primary_commit_result=primary,
        commit_order=genome.commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
        config=DeferredRetryShadowConfig(),
    )

    assert shadow.source_phase == PRIMARY_INCREMENTAL_COMMIT_PHASE
    assert shadow.observe_only is True
    assert shadow.candidate_count == 1
    assert len(shadow.candidates) == 1
    row = shadow.candidates[0]
    assert row.candidate_id == second.candidate_id
    assert row.conflict_reason == CommitConflictReason.REPROBE_FAILED.value
    assert row.original_commit_order == 1
    assert row.domain_snapshot_index == 1


def test_deferred_shadow_ignores_non_reprobe_conflicts(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    primary = CommitResult(
        committed_ids=(),
        reserved_route_cells=frozenset(),
        domain_version=0,
        conflicts=(
            CommitConflict("c1", CommitConflictReason.OCCUPIED_CELL_CONFLICT),
            CommitConflict(
                second.candidate_id,
                CommitConflictReason.REPROBE_FAILED,
            ),
        ),
    )
    shadow = build_deferred_retry_shadow_summary(
        primary_commit_result=primary,
        commit_order=("c1", second.candidate_id),
        candidates_by_id={second.candidate_id: second},
        inp=inp,
    )

    assert shadow.candidate_count == 1
    assert shadow.candidates[0].candidate_id == second.candidate_id
    assert shadow.ineligible_conflict_count == 1


def test_deferred_shadow_candidate_order_is_deterministic(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    candidates_by_id = {
        first.candidate_id: first,
        second.candidate_id: second,
    }
    primary = CommitResult(
        committed_ids=(first.candidate_id,),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict(
                second.candidate_id,
                CommitConflictReason.REPROBE_FAILED,
            ),
            CommitConflict(
                first.candidate_id,
                CommitConflictReason.REPROBE_FAILED,
            ),
        ),
    )
    shadow = build_deferred_retry_shadow_summary(
        primary_commit_result=primary,
        commit_order=(first.candidate_id, second.candidate_id),
        candidates_by_id=candidates_by_id,
        inp=inp,
    )

    assert [row.candidate_id for row in shadow.candidates] == [
        first.candidate_id,
        second.candidate_id,
    ]


def test_deferred_shadow_does_not_call_route_probe() -> None:
    primary = CommitResult(
        committed_ids=(),
        reserved_route_cells=frozenset(),
        domain_version=0,
        conflicts=(
            CommitConflict("x", CommitConflictReason.REPROBE_FAILED),
        ),
    )
    with patch(
        "django_apps.asteroid_lab.optimization.routing.route_probe.probe_route",
    ) as spy:
        build_deferred_retry_shadow_summary(
            primary_commit_result=primary,
            commit_order=("x",),
            candidates_by_id={},
            inp=replace(
                build_narrow_corridor_optimization_input(),
            ),
        )
    spy.assert_not_called()


def test_deferred_shadow_module_has_no_forbidden_imports() -> None:
    tree = ast.parse(_SHADOW_MODULE.read_text(encoding="utf-8-sig"))
    modules = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    assert not any("replay" in module for module in modules)
    assert not any("solver_summary" in module for module in modules)
    assert not any(module.endswith("route_probe") for module in modules)


def test_deferred_shadow_records_budget_and_domain_context(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    genome = PlacementGenome(
        commit_order=(first.candidate_id, second.candidate_id),
    )
    candidates_by_id = {
        first.candidate_id: first,
        second.candidate_id: second,
    }
    domain = initial_commit_domain(skeleton, inp)
    primary = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    shadow = build_deferred_retry_shadow_summary(
        primary_commit_result=primary,
        commit_order=genome.commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
    )

    assert shadow.budget.max_retry_rounds == 1
    assert shadow.budget.route_probe_max_expansions == 500
    assert shadow.domain_context["primary_commit_domain_version"] >= 1
    assert shadow.domain_context["eligible_reprobe_failed_count"] == 1


def test_deferred_shadow_does_not_change_commit_result(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    genome = PlacementGenome(
        commit_order=(first.candidate_id, second.candidate_id),
    )
    candidates_by_id = {
        first.candidate_id: first,
        second.candidate_id: second,
    }
    domain = initial_commit_domain(skeleton, inp)
    primary = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    before = (
        primary.committed_ids,
        primary.conflicts,
        primary.domain_version,
    )
    build_deferred_retry_shadow_summary(
        primary_commit_result=primary,
        commit_order=genome.commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
    )
    after = (
        primary.committed_ids,
        primary.conflicts,
        primary.domain_version,
    )
    assert before == after


def test_deferred_shadow_runs_before_lns_and_unchanged_by_lns(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    from django_apps.asteroid_lab.optimization import pipeline as pipeline_mod

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    fake_primary = CommitResult(
        committed_ids=(first.candidate_id,),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict(
                second.candidate_id,
                CommitConflictReason.REPROBE_FAILED,
            ),
        ),
    )
    lns_primary: list[CommitResult] = []

    def _fake_lns(
        _inp: OptimizationInput,
        _skeleton,
        genome,
        _candidates_by_id,
        commit_result,
        **kwargs,
    ):
        lns_primary.append(commit_result)
        return genome, commit_result

    fake_genome = PlacementGenome(
        commit_order=(first.candidate_id, second.candidate_id),
    )
    with (
        patch.object(
            pipeline_mod,
            "select_genome",
            return_value=fake_genome,
        ),
        patch.object(
            pipeline_mod,
            "incremental_commit",
            return_value=fake_primary,
        ),
        patch.object(pipeline_mod, "run_local_lns", side_effect=_fake_lns),
    ):
        result = pipeline_mod.run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        )

    assert len(lns_primary) == 1
    assert lns_primary[0] is fake_primary
    shadow = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    assert shadow["metrics"]["candidate_count"] == 1
    assert shadow["metrics"]["eligible_candidate_ids"] == [second.candidate_id]
