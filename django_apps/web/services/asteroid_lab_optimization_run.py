"""Run bounded asteroid optimization and append frames to the Lab replay track (single timeline)."""

from __future__ import annotations

import os
import time
from collections import Counter
from collections.abc import Mapping
from dataclasses import replace
from typing import Any, NamedTuple

from django.db import transaction

from django_apps.asteroid_lab.models import (
    AsteroidMapInput,
    ReplayFrame,
    ReplayTrack,
    UIPlaybackSession,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE
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
    OptimizationReplayFrame,
)
from django_apps.shapez_asteroid.optimization.enums import (
    EvolutionConvergenceReason,
    ExtractorPlacementPolicy,
    OptimizationReplayEventType,
    TransportKind,
)
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
_MAX_LAB_CANDIDATE_REJECTED_DETAIL_FRAMES = 24


class LabOptimizationRunResult(NamedTuple):
    """Result of ``run_lab_solver_optimization_for_map_input`` (counts + diagnostics)."""

    inspection_frame_count_before: int
    appended: int
    debug: dict[str, Any]


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


def _lab_max_consecutive_rejections() -> int | None:
    raw = os.environ.get("LAB_MAX_CONSECUTIVE_REJECTIONS", "64").strip()
    try:
        n = int(raw)
    except ValueError:
        return 64
    if n <= 0:
        return None
    return n


def _lab_run_solver_wall_clock_budget_ms() -> int | None:
    raw = os.environ.get("LAB_RUN_SOLVER_WALL_CLOCK_MS", "30000").strip()
    try:
        ms = int(raw)
    except ValueError:
        return 30000
    if ms <= 0:
        return None
    return ms


def _lab_run_solver_wall_clock_deadline_perf() -> float | None:
    ms = _lab_run_solver_wall_clock_budget_ms()
    if ms is None:
        return None
    return time.perf_counter() + (ms / 1000.0)


def _sorted_count_dict(pairs: tuple[tuple[str, int], ...]) -> dict[str, int]:
    return dict(pairs)


def _compress_rejected_candidate_replay_frames(
    frames: tuple[OptimizationReplayFrame, ...],
    *,
    max_detail: int = _MAX_LAB_CANDIDATE_REJECTED_DETAIL_FRAMES,
) -> tuple[OptimizationReplayFrame, ...]:
    """Cap ``candidate.rejected`` replay rows; append one summary frame when capped."""

    out: list[OptimizationReplayFrame] = []
    kept = 0
    omitted = 0
    omitted_reasons: Counter[str] = Counter()
    et_rejected = OptimizationReplayEventType.CANDIDATE_REJECTED
    for fr in frames:
        if fr.event_type != et_rejected:
            out.append(fr)
            continue
        if kept < max_detail:
            out.append(fr)
            kept += 1
            continue
        omitted += 1
        m = fr.metrics or {}
        raw_r = m.get("candidate_reject_reason")
        omitted_reasons[str(raw_r) if raw_r is not None else "unknown"] += 1
    if omitted:
        summary = OptimizationReplayFrame(
            frame_index=0,
            event_type=et_rejected,
            title="Candidate rejected (lab summary)",
            description=f"Omitted {omitted} additional rejected-candidate replay frames",
            visible_cells=(),
            overlay_cells=(),
            metrics={
                "lab_replay_compression": True,
                "omitted_candidate_rejected_frame_count": omitted,
                "omitted_candidate_reject_reason_counts": dict(omitted_reasons),
            },
        )
        out.append(summary)
    return tuple(replace(f, frame_index=i) for i, f in enumerate(out))


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
) -> LabOptimizationRunResult:
    """Run optimizer outside a DB txn; append frames inside ``transaction.atomic``."""

    deadline = _lab_run_solver_wall_clock_deadline_perf()
    gen_cfg = replace(
        _GEN_CFG,
        wall_clock_deadline_perf=deadline,
        max_consecutive_rejections=_lab_max_consecutive_rejections(),
    )
    evo_cfg = replace(_EVO_CFG, wall_clock_deadline_perf=deadline)

    t_build0 = time.perf_counter()
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
    build_input_ms = int((time.perf_counter() - t_build0) * 1000.0)

    rec = OptimizationReplayRecorder(max_frames=_MAX_LAB_OPTIMIZATION_REPLAY_FRAMES)
    t_gen0 = time.perf_counter()
    gen_out = generate_bundle_candidates(
        opt_input,
        route_domain,
        build_pattern_library(),
        gen_cfg,
        replay_recorder=rec,
    )
    candidate_generation_ms = int((time.perf_counter() - t_gen0) * 1000.0)

    pool = tuple(gen_out.normal_candidates)
    pool_n = len(pool)
    t_evo0 = time.perf_counter()
    evo = run_evolutionary_search(
        evo_cfg,
        pool,
        route_domain=route_domain,
        replay_recorder=rec,
    )
    evolution_ms = int((time.perf_counter() - t_evo0) * 1000.0)

    evo_reason = evo.convergence_reason
    t_cv0 = time.perf_counter()
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
    commit_validate_ms = int((time.perf_counter() - t_cv0) * 1000.0)

    raw_frames = tuple(rec.frames)
    if len(raw_frames) > _MAX_LAB_OPTIMIZATION_REPLAY_FRAMES:
        raw_frames = raw_frames[:_MAX_LAB_OPTIMIZATION_REPLAY_FRAMES]
    raw_frames = _compress_rejected_candidate_replay_frames(raw_frames)
    rec_n = len(raw_frames)

    diag = gen_out.diagnostics
    reject_dict: dict[str, int] = {}
    route_fail_dict: dict[str, int] = {}
    route_probe_ms_sum = 0
    gen_attempts = 0
    pre_dedupe_ok = 0
    unreachable_suppressed = 0
    enum_wall = False
    enum_consecutive = False
    if diag is not None:
        reject_dict = _sorted_count_dict(diag.reject_reason_counts)
        route_fail_dict = _sorted_count_dict(diag.route_probe_failure_reason_counts)
        route_probe_ms_sum = int(diag.route_probe_wall_ms_sum)
        gen_attempts = int(diag.enumeration_attempts)
        pre_dedupe_ok = int(diag.pre_dedupe_route_success_count)
        unreachable_suppressed = int(diag.route_probe_unreachable_suppressed_count)
        enum_wall = bool(diag.enumeration_aborted_wall_clock)
        enum_consecutive = bool(diag.enumeration_aborted_consecutive_rejects)

    first_10: list[dict[str, Any]] = []
    for row in gen_out.rejected_candidates[:10]:
        ext = row.extractor
        rp = row.route_probe_result
        first_10.append(
            {
                "attempted_pattern_id": row.attempted_pattern_id,
                "rejection_reason": row.rejection_reason.value,
                "extractor": None if ext is None else {"x": ext.x, "y": ext.y},
                "route_probe_failure_reason": (
                    None if rp is None or rp.failure_reason is None else rp.failure_reason.value
                ),
            }
        )

    stage = "completed"
    if enum_wall:
        stage = "candidate_generation_wall_clock"
    elif enum_consecutive:
        stage = "candidate_generation_consecutive_rejects"
    elif evo_reason is EvolutionConvergenceReason.WALL_CLOCK_DEADLINE:
        stage = "evolution_wall_clock"

    elapsed_ms = {
        "build_input": build_input_ms,
        "candidate_generation": candidate_generation_ms,
        "route_probe": route_probe_ms_sum,
        "evolution": evolution_ms,
        "commit_and_validate": commit_validate_ms,
        "attach": 0,
    }

    diagnostic_core: dict[str, Any] = {
        "stage": stage,
        "generated_candidate_count": gen_attempts,
        "normal_candidate_count": pool_n,
        "pre_dedupe_route_success_count": pre_dedupe_ok,
        "enumeration_aborted_wall_clock": enum_wall,
        "enumeration_aborted_consecutive_rejects": enum_consecutive,
        "rejected_candidate_count": len(gen_out.rejected_candidates) + unreachable_suppressed,
        "rejected_geometry_row_count": len(gen_out.rejected_candidates),
        "route_probe_unreachable_suppressed_count": unreachable_suppressed,
        "reject_reason_counts": reject_dict,
        "route_probe_failure_reason_counts": route_fail_dict,
        "first_10_rejected_candidates": first_10,
        "elapsed_ms": elapsed_ms,
        "lab_config": {
            "max_candidates": gen_cfg.max_candidates,
            "route_probe_max_expansions": gen_cfg.route_probe_max_expansions,
            "evolution_time_budget_ms": evo_cfg.time_budget_ms,
            "wall_clock_budget_ms": _lab_run_solver_wall_clock_budget_ms(),
            "max_consecutive_rejections": gen_cfg.max_consecutive_rejections,
        },
    }

    with transaction.atomic():
        ReplayTrack.objects.select_for_update().filter(pk=int(replay_track_id)).first()
        n0 = ReplayFrame.objects.filter(replay_track_id=int(replay_track_id)).count()
        cut = (
            ReplayFrame.objects.filter(
                replay_track_id=int(replay_track_id),
                frame_payload__event_type=EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
            )
            .order_by("frame_index", "id")
            .last()
        )
        if cut is None:
            msg = (
                f"ReplayTrack id={replay_track_id} has no reconstruction.map_complete frame; "
                "cannot reset lab replay before optimization append"
            )
            raise ValueError(msg)
        tail = ReplayFrame.objects.filter(
            replay_track_id=int(replay_track_id),
            frame_index__gt=int(cut.frame_index),
        )
        truncated_tail_frames = tail.count()
        tail.delete()
        sess = UIPlaybackSession.objects.filter(replay_track_id=int(replay_track_id)).first()
        if sess is not None:
            cap = int(cut.frame_index)
            if int(sess.current_frame_index) > cap:
                sess.current_frame_index = cap
                sess.save(update_fields=["current_frame_index", "updated_at"])
        baseline = _baseline_full_map_from_last_frame(cut)
        t_att0 = time.perf_counter()
        dtos = optimization_replay_frames_to_lab_append_dtos(
            raw_frames,
            baseline_full_map=baseline,
            commit_result=commit_res,
        )
        for dto in dtos:
            append_replay_frame(int(replay_track_id), dto)
        appended = len(dtos)
        attach_ms = int((time.perf_counter() - t_att0) * 1000.0)
        elapsed_ms["attach"] = attach_ms

        if appended > 0:
            reason = "appended"
        elif rec_n > 0:
            reason = "append_failed"
        elif pool_n == 0:
            reason = "empty_candidate_pool"
        elif rec_n == 0 and pool_n > 0 and int(evo.evaluated_genome_count) == 0:
            reason = "evolution_failed"
        else:
            reason = "empty_replay_frames"

        diagnostic = dict(diagnostic_core)
        diagnostic["elapsed_ms"] = dict(elapsed_ms)

        debug: dict[str, Any] = {
            "n0": n0,
            "truncated_tail_frames": truncated_tail_frames,
            "appended": appended,
            "reason": reason,
            "candidate_pool_len": pool_n,
            "recorder_frame_count": rec_n,
            "evolution_convergence_reason": str(evo_reason),
            "evaluated_genome_count": int(evo.evaluated_genome_count),
            "diagnostic": diagnostic,
        }
        return LabOptimizationRunResult(n0, appended, debug)


def build_optimization_replay_attach_payload(debug: Mapping[str, Any]) -> dict[str, Any]:
    """HTTP contract envelope (Lab); mirrors ``optimization_append_debug`` reason + diagnostic."""

    diag = debug.get("diagnostic")
    if not isinstance(diag, dict):
        diag = {}
    return {
        "reason": str(debug.get("reason", "")),
        "diagnostic": diag,
    }
