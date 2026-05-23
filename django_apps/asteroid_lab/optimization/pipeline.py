"""RTTP end-to-end pipeline wiring skeleton through validation (PR-5)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitResult,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.commit.local_lns import run_local_lns
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    genome: PlacementGenome
    commit_result: CommitResult
    normal_count: int
    validation_passed: bool


def run_rttp_pipeline(
    inp: OptimizationInput,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
) -> PipelineResult:
    """Wire skeleton → candidates → select → commit → (LNS if needed) → validate."""

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(inp, skeleton, policy=policy)
    genome = select_genome(generation.normal_candidates, skeleton, inp)
    candidates_by_id = {
        candidate.candidate_id: candidate
        for candidate in generation.normal_candidates
    }
    domain = initial_commit_domain(skeleton, inp)
    commit_result = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )

    if commit_result.conflicts:
        genome, commit_result = run_local_lns(
            inp,
            skeleton,
            genome,
            candidates_by_id,
            commit_result,
            policy=policy,
        )

    validation_passed = validate_final_layout(
        commit_result.committed_ids,
        commit_result.reserved_route_cells,
        candidates_by_id,
        inp,
    )

    return PipelineResult(
        genome=genome,
        commit_result=commit_result,
        normal_count=len(generation.normal_candidates),
        validation_passed=validation_passed,
    )


__all__ = ["PipelineResult", "run_rttp_pipeline"]
