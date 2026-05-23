"""RTTP end-to-end pipeline wiring skeleton through validation (PR-5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
from django_apps.asteroid_lab.optimization.replay_sink import (
    RttpReplaySink,
    resolve_replay_sink,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO


@dataclass(frozen=True, slots=True)
class PipelineResult:
    genome: PlacementGenome
    commit_result: CommitResult
    normal_count: int
    validation_passed: bool


def _record_replay(
    sink: RttpReplaySink,
    *,
    event_key: str,
    event_type: str,
    phase: str,
    title: str,
    metrics_json: dict[str, Any] | None = None,
) -> None:
    sink.record(
        SnapshotEventDTO(
            event_key=event_key,
            phase=phase,
            phase_step="",
            event_type=event_type,
            title=title,
            description="",
            metrics_json=dict(metrics_json or {}),
            cell_overlay_json={},
            full_map=[],
            is_decision_point=True,
        )
    )


def run_rttp_pipeline(
    inp: OptimizationInput,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    replay_sink: RttpReplaySink | None = None,
) -> PipelineResult:
    """Wire skeleton → candidates → select → commit → (LNS if needed) → validate."""

    sink = resolve_replay_sink(replay_sink)

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    _record_replay(
        sink,
        event_key="rttp-pipeline-start",
        event_type=et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        phase="rttp_pipeline",
        title="RTTP pipeline started",
        metrics_json={"skeleton_id": skeleton.skeleton_id},
    )

    generation = generate_candidates(inp, skeleton, policy=policy)
    _record_replay(
        sink,
        event_key="rttp-candidates",
        event_type=et.EVENT_TYPE_CANDIDATE_GENERATED,
        phase="candidate_generation",
        title="RTTP candidates generated",
        metrics_json={
            "normal_count": len(generation.normal_candidates),
            "rejected_count": len(generation.rejected_candidates),
        },
    )

    genome = select_genome(generation.normal_candidates, skeleton, inp)
    _record_replay(
        sink,
        event_key="rttp-selection",
        event_type=et.EVENT_TYPE_GA_BEST_UPDATED,
        phase="genome_fitness",
        title="RTTP selection complete",
        metrics_json={"commit_order": list(genome.commit_order)},
    )

    candidates_by_id = {
        candidate.candidate_id: candidate for candidate in generation.normal_candidates
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

    _record_replay(
        sink,
        event_key="rttp-commit-final",
        event_type=et.EVENT_TYPE_ROUTING_COMMITTED,
        phase="incremental_commit",
        title="RTTP commit complete",
        metrics_json={
            "committed_ids": list(commit_result.committed_ids),
            "commit_order": list(genome.commit_order),
            "validation_passed": validation_passed,
            "conflict_count": len(commit_result.conflicts),
            "normal_count": len(generation.normal_candidates),
        },
    )

    return PipelineResult(
        genome=genome,
        commit_result=commit_result,
        normal_count=len(generation.normal_candidates),
        validation_passed=validation_passed,
    )


__all__ = ["PipelineResult", "run_rttp_pipeline"]
