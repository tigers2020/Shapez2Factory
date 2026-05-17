"""Run bounded asteroid optimization and append frames to the Lab replay track (single timeline)."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from django_apps.asteroid_lab.models import AsteroidMapInput, ReplayFrame, ReplayTrack
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
)
from django_apps.asteroid_lab.services.optimization_replay_to_lab_frames import (
    optimization_replay_frames_to_lab_append_dtos,
)
from django_apps.asteroid_lab.services.replay_service import append_replay_frame
from django_apps.shapez_asteroid.adapters.reconstruction_adapter import build_optimization_input
from django_apps.shapez_asteroid.optimization.bundle_candidate_generator import (
    generate_bundle_candidates,
)
from django_apps.shapez_asteroid.optimization.dto import (
    CandidateGenerationConfig,
    EvolutionConfig,
)
from django_apps.shapez_asteroid.optimization.enums import ExtractorPlacementPolicy, TransportKind
from django_apps.shapez_asteroid.optimization.evolutionary_search import run_evolutionary_search
from django_apps.shapez_asteroid.optimization.final_validation import (
    validate_incremental_commit_result,
)
from django_apps.shapez_asteroid.optimization.incremental_commit import commit_best_genome
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplayRecorder
from django_apps.shapez_asteroid.optimization.pattern_library import build_pattern_library
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)
from django_apps.web.services.asteroid_lab_page_context import serialize_replay_frame

_MAX_LAB_OPTIMIZATION_REPLAY_FRAMES = 200

_GEN_CFG = CandidateGenerationConfig(
    extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
    allow_diagnostic_unreachable=False,
    max_candidates=32,
    route_probe_max_expansions=500,
    transport_kinds=frozenset({TransportKind.SHAPE_BELT, TransportKind.FLUID_PIPE}),
    route_probe_goal_priority_weight=10,
)

_EVO_CFG = EvolutionConfig(
    seed=4242,
    population_size=6,
    elite_count=2,
    mutation_rate=0.25,
    tournament_size=2,
    max_generation=3,
    max_stall_generation=2,
    time_budget_ms=8000,
    forced_distant_mutation_period=None,
)


def _baseline_full_map_from_last_frame(last: ReplayFrame) -> list[dict[str, Any]]:
    ser = serialize_replay_frame(last)
    fm = ser.get("full_map")
    if isinstance(fm, list) and fm:
        return [dict(r) if isinstance(r, dict) else {} for r in fm]
    co = dict(last.cell_overlay_json or {})
    cells = co.get("cells")
    if isinstance(cells, list):
        return [dict(r) if isinstance(r, dict) else {} for r in cells]
    return []


def run_lab_solver_optimization_for_map_input(
    *,
    map_input_id: int,
    replay_track_id: int,
) -> tuple[int, int]:
    """Run optimizer outside DB txn; append Lab ``ReplayFrame`` rows inside ``transaction.atomic``.

    Returns ``(inspection_frame_count_before, appended_count)``.
    """

    inp = AsteroidMapInput.objects.filter(pk=int(map_input_id)).select_related("project").first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)
    track = ReplayTrack.objects.filter(pk=int(replay_track_id)).first()
    if track is None or int(track.project_id) != int(inp.project_id):
        raise ValueError("replay_track_not_found_or_project_mismatch")

    snapshot = build_decoded_blueprint_snapshot_from_input(int(map_input_id))
    cleanup = load_cleanup_result(snapshot)
    recon = run_topology_reconstruction(cleanup)
    opt_input = build_optimization_input(recon, cleanup)
    route_domain = RouteDomainSnapshotBuilder.build_seed_snapshot(opt_input)

    rec = OptimizationReplayRecorder(max_frames=_MAX_LAB_OPTIMIZATION_REPLAY_FRAMES)
    gen_out = generate_bundle_candidates(
        opt_input,
        route_domain,
        build_pattern_library(),
        _GEN_CFG,
        replay_recorder=rec,
    )
    pool = tuple(gen_out.normal_candidates)
    evo = run_evolutionary_search(
        _EVO_CFG,
        pool,
        route_domain=route_domain,
        replay_recorder=rec,
    )
    commit_res = commit_best_genome(
        evo.best_genome,
        pool,
        opt_input,
        RouteDomainSnapshotBuilder,
        replay_recorder=rec,
    )
    validate_incremental_commit_result(
        opt_input,
        pool,
        commit_res,
        replay_recorder=rec,
    )

    raw_frames = tuple(rec.frames)
    if len(raw_frames) > _MAX_LAB_OPTIMIZATION_REPLAY_FRAMES:
        raw_frames = raw_frames[:_MAX_LAB_OPTIMIZATION_REPLAY_FRAMES]

    with transaction.atomic():
        ReplayTrack.objects.select_for_update().filter(pk=int(replay_track_id)).first()
        n0 = ReplayFrame.objects.filter(replay_track_id=int(replay_track_id)).count()
        last = (
            ReplayFrame.objects.filter(replay_track_id=int(replay_track_id))
            .order_by("-frame_index", "-id")
            .first()
        )
        if last is None:
            msg = f"ReplayTrack id={replay_track_id} has no frames; cannot resolve baseline map"
            raise ValueError(msg)
        baseline = _baseline_full_map_from_last_frame(last)
        dtos = optimization_replay_frames_to_lab_append_dtos(
            raw_frames,
            baseline_full_map=baseline,
            commit_result=commit_res,
        )
        for dto in dtos:
            append_replay_frame(int(replay_track_id), dto)
        return n0, len(dtos)
