"""12D — Run GA after successful inspection replay, then persist optimization replay (output-only).

``replay_pipeline_service`` must not import ``django_apps.shapez_asteroid``; this module lives in
``web.services`` and may orchestrate shapez_asteroid + attach (12C).
"""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
)
from django_apps.asteroid_lab.services.dto import InitialReplayPipelineResultDTO
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    OptimizationReplayAttachResult,
    attach_optimization_replay_frames_after_successful_replay_build,
)
from django_apps.shapez_asteroid.adapters.reconstruction_adapter import build_optimization_input
from django_apps.shapez_asteroid.optimization.bundle_candidate_generator import (
    generate_bundle_candidates,
)
from django_apps.shapez_asteroid.optimization.dto import CandidateGenerationConfig, EvolutionConfig
from django_apps.shapez_asteroid.optimization.enums import ExtractorPlacementPolicy, TransportKind
from django_apps.shapez_asteroid.optimization.evolutionary_search import run_evolutionary_search
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplayRecorder
from django_apps.shapez_asteroid.optimization.pattern_library import build_pattern_library
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)


def run_post_inspection_evolution_and_attach_optimization_replay(
    map_input_id: int,
    pipeline_result: InitialReplayPipelineResultDTO,
) -> OptimizationReplayAttachResult:
    """If inspection replay succeeded, run a bounded GA pass and persist replay frames.

    Failures during evolution do not raise: the user import/replay path still succeeds.
    """

    if pipeline_result.status != "ok":
        return OptimizationReplayAttachResult(attached=False, reason="non_ok_result")
    if pipeline_result.solver_run_id is None:
        return OptimizationReplayAttachResult(attached=False, reason="missing_solver_run_id")

    try:
        snapshot = build_decoded_blueprint_snapshot_from_input(int(map_input_id))
        cleanup = deconstruct_snapshot(snapshot)
        recon = reconstruct_snapshot(snapshot)
        opt_input = build_optimization_input(recon, cleanup)
        domain = RouteDomainSnapshotBuilder.build_seed_snapshot(opt_input)
        recorder = OptimizationReplayRecorder()
        gen_cfg = CandidateGenerationConfig(
            extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
            allow_diagnostic_unreachable=True,
            max_candidates=64,
            route_probe_max_expansions=200,
            transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
            route_probe_goal_priority_weight=10,
        )
        pool_result = generate_bundle_candidates(
            opt_input,
            domain,
            build_pattern_library(),
            gen_cfg,
            replay_recorder=recorder,
        )
        pool = pool_result.normal_candidates
        evo_cfg = EvolutionConfig(
            seed=42,
            population_size=4,
            elite_count=1,
            mutation_rate=0.5,
            tournament_size=2,
            max_generation=1,
            max_stall_generation=0,
            time_budget_ms=1200,
            forced_distant_mutation_period=None,
        )
        run_evolutionary_search(evo_cfg, pool, replay_recorder=recorder, route_domain=domain)
    except Exception:
        return OptimizationReplayAttachResult(attached=False, reason="evolution_failed")

    return attach_optimization_replay_frames_after_successful_replay_build(
        pipeline_result, recorder.frames
    )


__all__ = ["run_post_inspection_evolution_and_attach_optimization_replay"]
