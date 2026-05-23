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
from django_apps.asteroid_lab.optimization.rttp_replay_diagnostics import (
    build_candidates_replay_payload,
    build_commit_replay_payload,
    build_pipeline_start_replay_payload,
    build_selection_replay_payload,
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
    description: str = "",
    metrics_json: dict[str, Any] | None = None,
    cell_overlay_json: dict[str, Any] | None = None,
) -> None:
    sink.record(
        SnapshotEventDTO(
            event_key=event_key,
            phase=phase,
            phase_step="",
            event_type=event_type,
            title=title,
            description=description,
            metrics_json=dict(metrics_json or {}),
            cell_overlay_json=dict(cell_overlay_json or {}),
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
    start_payload = build_pipeline_start_replay_payload(skeleton)
    _record_replay(
        sink,
        event_key="rttp-pipeline-start",
        event_type=et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        phase="rttp_pipeline",
        title="RTTP pipeline started",
        description=start_payload.description,
        metrics_json={"skeleton_id": skeleton.skeleton_id},
        cell_overlay_json=start_payload.cell_overlay_json,
    )

    generation = generate_candidates(inp, skeleton, policy=policy)
    candidates_payload = build_candidates_replay_payload(generation)
    _record_replay(
        sink,
        event_key="rttp-candidates",
        event_type=et.EVENT_TYPE_CANDIDATE_GENERATED,
        phase="candidate_generation",
        title="RTTP candidates generated",
        description=candidates_payload.description,
        metrics_json={
            "normal_count": len(generation.normal_candidates),
            "rejected_count": len(generation.rejected_candidates),
        },
        cell_overlay_json=candidates_payload.cell_overlay_json,
    )

    genome = select_genome(generation.normal_candidates, skeleton, inp)
    selection_payload = build_selection_replay_payload(genome, generation.normal_candidates)
    _record_replay(
        sink,
        event_key="rttp-selection",
        event_type=et.EVENT_TYPE_GA_BEST_UPDATED,
        phase="genome_fitness",
        title="RTTP selection complete",
        description=selection_payload.description,
        metrics_json={"commit_order": list(genome.commit_order)},
        cell_overlay_json=selection_payload.cell_overlay_json,
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

    commit_payload = build_commit_replay_payload(
        commit_result,
        validation_passed=validation_passed,
        normal_count=len(generation.normal_candidates),
        commit_order=tuple(genome.commit_order),
    )
    _record_replay(
        sink,
        event_key="rttp-commit-final",
        event_type=et.EVENT_TYPE_ROUTING_COMMITTED,
        phase="incremental_commit",
        title="RTTP commit complete",
        description=commit_payload.description,
        metrics_json={
            "committed_ids": list(commit_result.committed_ids),
            "commit_order": list(genome.commit_order),
            "validation_passed": validation_passed,
            "conflict_count": len(commit_result.conflicts),
            "normal_count": len(generation.normal_candidates),
        },
        cell_overlay_json=commit_payload.cell_overlay_json,
    )

    return PipelineResult(
        genome=genome,
        commit_result=commit_result,
        normal_count=len(generation.normal_candidates),
        validation_passed=validation_passed,
    )


__all__ = ["PipelineResult", "run_rttp_pipeline"]
