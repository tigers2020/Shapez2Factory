"""Bundle candidate enumeration with immediate route probe (Sequence 3)."""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Mapping, Sequence

from django_apps.shapez_asteroid.optimization.bundle_candidate_factory import (
    make_reachable_bundle_candidate,
)
from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    CandidateEquivalenceKey,
    CandidateGenerationConfig,
    CandidateGenerationDiagnostics,
    CandidateGenerationResult,
    OptimizationInput,
    RejectedBundleCandidate,
    RouteCellDomain,
    RouteProbeInput,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    OptimizationReplayEventType,
)
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    OptimizationReplaySink,
)
from django_apps.shapez_asteroid.optimization.optimization_replay_events import (
    emit_optimization_input_loaded,
    optimization_input_loaded_metrics,
)
from django_apps.shapez_asteroid.optimization.pattern_dto import BundlePattern
from django_apps.shapez_asteroid.optimization.route_probe import run_route_probe
from django_apps.shapez_asteroid.optimization.topology_signature import build_topology_signature


def _add(a: Coord, b: Coord) -> Coord:
    return Coord(a.x + b.x, a.y + b.y)


def _equivalence_key(c: BundleCandidate) -> CandidateEquivalenceKey:
    return CandidateEquivalenceKey(
        occupied_cells=c.occupied_cells,
        output_stub=c.output_stub,
        output_dir=c.output_dir,
        transport_kind=c.transport_kind,
        base_throughput=c.base_throughput,
        topology_signature=c.topology_signature,
    )


def _replay_emit(
    recorder: OptimizationReplaySink | None,
    *,
    event_type: OptimizationReplayEventType,
    title: str,
    description: str,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    metrics: dict[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    recorder.record_replay_frame(
        event_type=event_type,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=metrics,
    )


def _replay_geometry_row(
    coord: Coord,
    *,
    overlay_role: str,
    severity: str = "info",
) -> dict[str, object]:
    return {
        "x": int(coord.x),
        "y": int(coord.y),
        "layer": 0,
        "rotation": 0,
        "overlay_role": overlay_role,
        "severity": severity,
    }


def _geometry_attempt_cells(
    occupied: frozenset[Coord],
    output_stub: Coord,
    path: tuple[Coord, ...] = (),
    *,
    path_overlay_role: str = "route_path",
    footprint_severity: str = "warn",
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    """visible: occupied + stub; overlay: route path (Lab 2D optimization overlay)."""
    visible: list[object] = [
        _replay_geometry_row(c, overlay_role="candidate_occupied", severity=footprint_severity)
        for c in sorted(occupied, key=lambda z: (z.x, z.y))
    ]
    visible.append(
        _replay_geometry_row(output_stub, overlay_role="output_stub", severity=footprint_severity)
    )
    overlay: list[object] = [
        _replay_geometry_row(step, overlay_role=path_overlay_role, severity="info") for step in path
    ]
    return (tuple(visible), tuple(overlay))


def generate_bundle_candidates(
    opt: OptimizationInput,
    route_domain: Mapping[Coord, RouteCellDomain],
    patterns: Sequence[BundlePattern],
    config: CandidateGenerationConfig,
    replay_recorder: OptimizationReplaySink | None = None,
) -> CandidateGenerationResult:
    """Enumerate candidates, probe immediately, split normal vs rejected (no placement commit).

    ``allow_diagnostic_unreachable``: when True, route-probe failures are appended to
    ``rejected_candidates`` with ``ROUTE_PROBE_UNREACHABLE``. When False, those rows are omitted
    (geometry rejects are always recorded).
    """

    if config.extractor_policy is not ExtractorPlacementPolicy.RIM_ONLY:
        raise ValueError("v0 only supports ExtractorPlacementPolicy.RIM_ONLY")

    emit_optimization_input_loaded(
        replay_recorder,
        extra_metrics=optimization_input_loaded_metrics(opt),
    )

    rim_order = tuple(sorted(opt.rim_cells, key=lambda c: (c.x, c.y)))
    tk_order = tuple(sorted(config.transport_kinds, key=lambda k: k.value))

    normal_raw: list[BundleCandidate] = []
    rejected: list[RejectedBundleCandidate] = []
    reject_counts: Counter[str] = Counter()
    route_fail_counts: Counter[str] = Counter()
    route_unreachable_suppressed = 0
    route_probe_wall_ms_sum = 0

    def _reject(row: RejectedBundleCandidate) -> None:
        reject_counts[row.rejection_reason.value] += 1
        rejected.append(row)

    seq = 0
    abort_enum = False
    abort_consecutive = False
    consecutive_streak = 0

    def _fail_attempt() -> None:
        nonlocal consecutive_streak, abort_consecutive
        consecutive_streak += 1
        lim = config.max_consecutive_rejections
        if lim is not None and lim > 0 and consecutive_streak >= lim:
            abort_consecutive = True
            _replay_emit(
                replay_recorder,
                event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                title="Enumeration stopped",
                description=(
                    f"{consecutive_streak} consecutive failures without a normal candidate"
                ),
                metrics={
                    "lab_abort_reason": "consecutive_rejects",
                    "consecutive_reject_streak": consecutive_streak,
                    "max_consecutive_rejections": lim,
                },
            )

    for rim_cell in rim_order:
        if abort_enum or abort_consecutive:
            break
        for pattern in patterns:
            if abort_enum or abort_consecutive:
                break
            for tk in tk_order:
                if abort_enum or abort_consecutive:
                    break
                if config.wall_clock_deadline_perf is not None and time.perf_counter() >= (
                    config.wall_clock_deadline_perf
                ):
                    abort_enum = True
                    break
                seq += 1
                candidate_id = f"c{seq:09d}"
                extractor = _add(rim_cell, pattern.extractor_offset)
                extensions = tuple(_add(rim_cell, o) for o in pattern.extension_offsets)
                occupied = frozenset({extractor, *extensions})
                output_stub = _add(rim_cell, pattern.output_stub_offset)

                if extractor not in opt.rim_cells:
                    _reject(
                        RejectedBundleCandidate(
                            attempted_pattern_id=pattern.pattern_id,
                            extractor=extractor,
                            rejection_reason=CandidateRejectReason.EXTRACTOR_NOT_RIM,
                            route_probe_result=None,
                        )
                    )
                    vis, ovl = _geometry_attempt_cells(occupied, output_stub, ())
                    _replay_emit(
                        replay_recorder,
                        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                        title="Candidate rejected",
                        description="Extractor not on rim",
                        visible_cells=vis,
                        overlay_cells=ovl,
                        metrics={
                            "pattern_id": pattern.pattern_id,
                            "transport_kind": tk,
                            "candidate_reject_reason": CandidateRejectReason.EXTRACTOR_NOT_RIM,
                            "candidate_id": candidate_id,
                        },
                    )
                    _fail_attempt()
                    if abort_consecutive:
                        break
                    continue

                if any(e not in opt.mineable_cells for e in extensions):
                    _reject(
                        RejectedBundleCandidate(
                            attempted_pattern_id=pattern.pattern_id,
                            extractor=extractor,
                            rejection_reason=CandidateRejectReason.EXTENSION_NOT_MINEABLE,
                            route_probe_result=None,
                        )
                    )
                    vis, ovl = _geometry_attempt_cells(occupied, output_stub, ())
                    _replay_emit(
                        replay_recorder,
                        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                        title="Candidate rejected",
                        description="Extension not mineable",
                        visible_cells=vis,
                        overlay_cells=ovl,
                        metrics={
                            "pattern_id": pattern.pattern_id,
                            "transport_kind": tk,
                            "candidate_reject_reason": CandidateRejectReason.EXTENSION_NOT_MINEABLE,
                            "candidate_id": candidate_id,
                        },
                    )
                    _fail_attempt()
                    if abort_consecutive:
                        break
                    continue

                if not occupied.issubset(opt.asteroid_cells):
                    _reject(
                        RejectedBundleCandidate(
                            attempted_pattern_id=pattern.pattern_id,
                            extractor=extractor,
                            rejection_reason=CandidateRejectReason.OCCUPIED_OUTSIDE_ASTEROID,
                            route_probe_result=None,
                        )
                    )
                    vis, ovl = _geometry_attempt_cells(occupied, output_stub, ())
                    _replay_emit(
                        replay_recorder,
                        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                        title="Candidate rejected",
                        description="Occupied outside asteroid",
                        visible_cells=vis,
                        overlay_cells=ovl,
                        metrics={
                            "pattern_id": pattern.pattern_id,
                            "transport_kind": tk,
                            "candidate_reject_reason": (
                                CandidateRejectReason.OCCUPIED_OUTSIDE_ASTEROID
                            ),
                            "candidate_id": candidate_id,
                        },
                    )
                    _fail_attempt()
                    if abort_consecutive:
                        break
                    continue

                if len(occupied) != 1 + pattern.extension_count:
                    _reject(
                        RejectedBundleCandidate(
                            attempted_pattern_id=pattern.pattern_id,
                            extractor=extractor,
                            rejection_reason=CandidateRejectReason.PATTERN_OVERLAP_SELF,
                            route_probe_result=None,
                        )
                    )
                    vis, ovl = _geometry_attempt_cells(occupied, output_stub, ())
                    _replay_emit(
                        replay_recorder,
                        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                        title="Candidate rejected",
                        description="Pattern self-overlap",
                        visible_cells=vis,
                        overlay_cells=ovl,
                        metrics={
                            "pattern_id": pattern.pattern_id,
                            "transport_kind": tk,
                            "candidate_reject_reason": CandidateRejectReason.PATTERN_OVERLAP_SELF,
                            "candidate_id": candidate_id,
                        },
                    )
                    _fail_attempt()
                    if abort_consecutive:
                        break
                    continue

                if output_stub in occupied:
                    _reject(
                        RejectedBundleCandidate(
                            attempted_pattern_id=pattern.pattern_id,
                            extractor=extractor,
                            rejection_reason=CandidateRejectReason.OUTPUT_STUB_INSIDE_OCCUPIED,
                            route_probe_result=None,
                        )
                    )
                    vis, ovl = _geometry_attempt_cells(occupied, output_stub, ())
                    _replay_emit(
                        replay_recorder,
                        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                        title="Candidate rejected",
                        description="Output stub inside occupied",
                        visible_cells=vis,
                        overlay_cells=ovl,
                        metrics={
                            "pattern_id": pattern.pattern_id,
                            "transport_kind": tk,
                            "candidate_reject_reason": (
                                CandidateRejectReason.OUTPUT_STUB_INSIDE_OCCUPIED
                            ),
                            "candidate_id": candidate_id,
                        },
                    )
                    _fail_attempt()
                    if abort_consecutive:
                        break
                    continue

                if output_stub not in route_domain:
                    _reject(
                        RejectedBundleCandidate(
                            attempted_pattern_id=pattern.pattern_id,
                            extractor=extractor,
                            rejection_reason=CandidateRejectReason.OUTPUT_STUB_INVALID_COORD,
                            route_probe_result=None,
                        )
                    )
                    vis, ovl = _geometry_attempt_cells(occupied, output_stub, ())
                    _replay_emit(
                        replay_recorder,
                        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                        title="Candidate rejected",
                        description="Output stub invalid coord",
                        visible_cells=vis,
                        overlay_cells=ovl,
                        metrics={
                            "pattern_id": pattern.pattern_id,
                            "transport_kind": tk,
                            "candidate_reject_reason": (
                                CandidateRejectReason.OUTPUT_STUB_INVALID_COORD
                            ),
                            "candidate_id": candidate_id,
                        },
                    )
                    _fail_attempt()
                    if abort_consecutive:
                        break
                    continue

                topo_sig = build_topology_signature(
                    pattern=pattern,
                    transport_kind=tk,
                    base_throughput=pattern.throughput_factor,
                    absolute_occupied=occupied,
                    output_stub=output_stub,
                    output_dir=pattern.output_dir,
                )

                probe_inp = RouteProbeInput(
                    start=output_stub,
                    goals=opt.route_goals,
                    route_domain=route_domain,
                    topology_graph=opt.topology_graph,
                    max_expansions=config.route_probe_max_expansions,
                    transport_kind=tk,
                    goal_priority_weight=config.route_probe_goal_priority_weight,
                    wall_clock_deadline_perf=config.wall_clock_deadline_perf,
                )
                rp_t0 = time.perf_counter()
                probe_res = run_route_probe(probe_inp, occupied_cells=occupied)
                route_probe_wall_ms_sum += int((time.perf_counter() - rp_t0) * 1000.0)

                probe_base_metrics: dict[str, object] = {
                    "pattern_id": pattern.pattern_id,
                    "topology_signature": topo_sig,
                    "transport_kind": tk,
                    "route_cost": probe_res.cost,
                    "expanded_nodes": probe_res.expanded_nodes,
                }
                if probe_res.reached_goal is not None:
                    probe_base_metrics["reached_goal_kind"] = probe_res.reached_goal.goal_kind
                else:
                    probe_base_metrics["reached_goal_kind"] = None
                probe_base_metrics["goal_priority"] = probe_res.goal_priority

                if not probe_res.reachable or probe_res.reached_goal is None:
                    fr = probe_res.failure_reason
                    if fr is not None:
                        route_fail_counts[fr.value] += 1
                    fail_metrics = {
                        **probe_base_metrics,
                        "route_probe_failure_reason": probe_res.failure_reason,
                        "candidate_id": candidate_id,
                    }
                    vis, ovl = _geometry_attempt_cells(
                        occupied,
                        output_stub,
                        probe_res.path,
                        footprint_severity="error",
                    )
                    _replay_emit(
                        replay_recorder,
                        event_type=OptimizationReplayEventType.ROUTE_PROBE_FAILED,
                        title="Route probe failed",
                        description="No reachable goal from output stub",
                        visible_cells=vis,
                        overlay_cells=ovl,
                        metrics=fail_metrics,
                    )
                    if config.allow_diagnostic_unreachable:
                        _reject(
                            RejectedBundleCandidate(
                                attempted_pattern_id=pattern.pattern_id,
                                extractor=extractor,
                                rejection_reason=CandidateRejectReason.ROUTE_PROBE_UNREACHABLE,
                                route_probe_result=probe_res,
                            )
                        )
                        vis, ovl = _geometry_attempt_cells(
                            occupied,
                            output_stub,
                            probe_res.path,
                            footprint_severity="error",
                        )
                        _replay_emit(
                            replay_recorder,
                            event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
                            title="Candidate rejected",
                            description="Route probe unreachable (diagnostic)",
                            visible_cells=vis,
                            overlay_cells=ovl,
                            metrics={
                                **probe_base_metrics,
                                "candidate_reject_reason": (
                                    CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
                                ),
                                "route_probe_failure_reason": probe_res.failure_reason,
                                "candidate_id": candidate_id,
                            },
                        )
                    if not config.allow_diagnostic_unreachable:
                        route_unreachable_suppressed += 1
                    _fail_attempt()
                    if abort_consecutive:
                        break
                    continue

                ok_metrics = {
                    **probe_base_metrics,
                    "route_probe_failure_reason": None,
                    "candidate_id": candidate_id,
                }
                vis_ok, ovl_ok = _geometry_attempt_cells(
                    occupied,
                    output_stub,
                    probe_res.path,
                    footprint_severity="info",
                )
                _replay_emit(
                    replay_recorder,
                    event_type=OptimizationReplayEventType.ROUTE_PROBE_SUCCEEDED,
                    title="Route probe succeeded",
                    description="Reachable route goal from output stub",
                    visible_cells=vis_ok,
                    overlay_cells=ovl_ok,
                    metrics=ok_metrics,
                )

                cand = make_reachable_bundle_candidate(
                    candidate_id=candidate_id,
                    pattern_id=pattern.pattern_id,
                    topology_signature=topo_sig,
                    extractor=extractor,
                    extensions=extensions,
                    occupied_cells=occupied,
                    output_stub=output_stub,
                    output_dir=pattern.output_dir,
                    transport_kind=tk,
                    base_throughput=pattern.throughput_factor,
                    base_score=float(pattern.throughput_factor),
                    route_probe_result=probe_res,
                )
                normal_raw.append(cand)
                consecutive_streak = 0
                vis_c, ovl_c = _geometry_attempt_cells(
                    occupied,
                    output_stub,
                    probe_res.path,
                    footprint_severity="info",
                )
                _replay_emit(
                    replay_recorder,
                    event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
                    title="Candidate generated",
                    description="Normal pool candidate after route probe",
                    visible_cells=vis_c,
                    overlay_cells=ovl_c,
                    metrics={
                        "candidate_id": candidate_id,
                        "pattern_id": pattern.pattern_id,
                        "topology_signature": topo_sig,
                        "transport_kind": tk,
                        "reached_goal_kind": (
                            probe_res.reached_goal.goal_kind if probe_res.reached_goal else None
                        ),
                        "goal_priority": probe_res.goal_priority,
                        "route_probe_failure_reason": None,
                        "candidate_reject_reason": None,
                        "route_cost": probe_res.cost,
                        "expanded_nodes": probe_res.expanded_nodes,
                    },
                )

            if abort_enum or abort_consecutive:
                break
        if abort_enum or abort_consecutive:
            break

    by_key: dict[CandidateEquivalenceKey, BundleCandidate] = {}
    for c in sorted(normal_raw, key=lambda z: z.candidate_id):
        k = _equivalence_key(c)
        prev = by_key.get(k)
        if prev is None or c.candidate_id < prev.candidate_id:
            by_key[k] = c

    deduped = tuple(sorted(by_key.values(), key=lambda z: z.candidate_id))
    sorted_for_cap = sorted(
        deduped,
        key=lambda c: (-c.base_score, c.route_probe_result.cost, c.candidate_id),
    )
    if config.max_candidates is not None:
        sorted_for_cap = sorted_for_cap[: config.max_candidates]
    normal_final = tuple(sorted_for_cap)

    def _sorted_counts(c: Counter[str]) -> tuple[tuple[str, int], ...]:
        return tuple(sorted(c.items(), key=lambda kv: kv[0]))

    diagnostics = CandidateGenerationDiagnostics(
        enumeration_attempts=seq,
        pre_dedupe_route_success_count=len(normal_raw),
        route_probe_unreachable_suppressed_count=route_unreachable_suppressed,
        reject_reason_counts=_sorted_counts(reject_counts),
        route_probe_failure_reason_counts=_sorted_counts(route_fail_counts),
        enumeration_aborted_wall_clock=abort_enum,
        enumeration_aborted_consecutive_rejects=abort_consecutive,
        max_consecutive_rejections=config.max_consecutive_rejections,
        route_probe_wall_ms_sum=route_probe_wall_ms_sum,
    )

    return CandidateGenerationResult(
        normal_candidates=normal_final,
        rejected_candidates=tuple(rejected),
        diagnostics=diagnostics,
    )
