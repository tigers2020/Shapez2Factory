"""Sequence 6 — incremental route commit (best genome → confirmed routes)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    CandidateCommitResult,
    CandidateGenerationConfig,
    CommittedPlacement,
    Gene,
    Genome,
    IncrementalCommitResult,
    OptimizationInput,
    RecoveryBudget,
    RouteCellDomain,
    RouteDomainCellTransition,
    RouteProbeInput,
    RouteProbeResult,
    RouteReservation,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CommitConflictReason,
    ExtractorPlacementPolicy,
    PlacementCommitState,
    ReservationState,
    RouteProbeFailureReason,
    TransportKind,
    TransportMask,
)
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplaySink
from django_apps.shapez_asteroid.optimization.optimization_replay_events import (
    emit_route_commit_attempted,
    emit_route_committed,
    emit_route_rolled_back,
)
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)
from django_apps.shapez_asteroid.optimization.route_probe import run_route_probe

_DEFAULT_PROBE_CFG = CandidateGenerationConfig(
    extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
    allow_diagnostic_unreachable=False,
    max_candidates=None,
    route_probe_max_expansions=500,
    transport_kinds=frozenset({TransportKind.SHAPE_BELT, TransportKind.FLUID_PIPE}),
    route_probe_goal_priority_weight=10,
)


def _pool_by_id(pool: Sequence[BundleCandidate]) -> dict[str, BundleCandidate]:
    out: dict[str, BundleCandidate] = {}
    for c in sorted(pool, key=lambda z: z.candidate_id):
        if c.candidate_id in out:
            raise ValueError(f"duplicate candidate_id in pool: {c.candidate_id!r}")
        out[c.candidate_id] = c
    return out


def genome_commit_candidates(
    genome: Genome,
    candidate_pool: Sequence[BundleCandidate],
) -> tuple[tuple[Gene, BundleCandidate], ...]:
    """Commit order: ``commit_order`` ASC, then ``candidate_id`` ASC (not fitness order)."""

    by_id = _pool_by_id(candidate_pool)
    pairs: list[tuple[Gene, BundleCandidate]] = []
    for g in sorted(genome.genes, key=lambda z: (z.commit_order, z.candidate_id)):
        if not g.enabled or g.candidate_id not in by_id:
            continue
        pairs.append((g, by_id[g.candidate_id]))
    return tuple(pairs)


def _mask_allows(mask: TransportMask, kind: TransportKind) -> bool:
    if kind is TransportKind.SHAPE_BELT:
        return bool(mask & TransportMask.SHAPE_BELT)
    if kind is TransportKind.FLUID_PIPE:
        return bool(mask & TransportMask.FLUID_PIPE)
    return False


def _domain_diff_route_classes(
    before: Mapping[Coord, RouteCellDomain],
    after: Mapping[Coord, RouteCellDomain],
) -> tuple[RouteDomainCellTransition, ...]:
    keys = set(before.keys()) | set(after.keys())
    out: list[RouteDomainCellTransition] = []
    for c in sorted(keys, key=lambda z: (z.x, z.y)):
        b = before.get(c)
        a = after.get(c)
        if b is None or a is None:
            continue
        if b.route_class != a.route_class:
            out.append(
                RouteDomainCellTransition(
                    coord=c, route_class_before=b.route_class, route_class_after=a.route_class
                )
            )
    return tuple(out)


def _probe_connected(res: RouteProbeResult) -> bool:
    if not res.reachable or not res.path:
        return False
    if res.reached_goal is None or res.goal_priority is None:
        return False
    return res.failure_reason is None


def _budget_probe_failure() -> RouteProbeResult:
    return RouteProbeResult(
        reachable=False,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=None,
        goal_priority=None,
        failure_reason=RouteProbeFailureReason.EXHAUSTED,
    )


def _path_conflict_reason(
    *,
    inp: OptimizationInput,
    cand: BundleCandidate,
    path: tuple[Coord, ...],
    route_domain: Mapping[Coord, RouteCellDomain],
    committed_occupied: frozenset[Coord],
    confirmed_reservations: tuple[RouteReservation, ...],
) -> CommitConflictReason | None:
    path_set = set(path)
    if path_set & cand.occupied_cells:
        return CommitConflictReason.OCCUPIED_CELL_CONFLICT
    if path_set & committed_occupied:
        return CommitConflictReason.OCCUPIED_CELL_CONFLICT
    for c in path:
        if c in inp.blocked_cells:
            return CommitConflictReason.HARD_BLOCKED_CONFLICT
        dom = route_domain.get(c)
        if dom is None:
            return CommitConflictReason.ROUTE_PROBE_FAILED
        if not _mask_allows(dom.transport_mask, cand.transport_kind):
            return CommitConflictReason.TRANSPORT_KIND_CONFLICT
    for other in confirmed_reservations:
        if other.candidate_id == cand.candidate_id:
            continue
        inter = path_set & other.reserved_cells
        if inter and other.transport_kind is not cand.transport_kind:
            return CommitConflictReason.ROUTE_CELL_CONFLICT
    return None


def _invoke_build_commit(
    cls_or: RouteDomainSnapshotBuilder | type[RouteDomainSnapshotBuilder],
    inp: OptimizationInput,
    confirmed: tuple[RouteReservation, ...],
    occupied: frozenset[Coord],
) -> dict[Coord, RouteCellDomain]:
    cls: type[RouteDomainSnapshotBuilder] = cls_or if isinstance(cls_or, type) else type(cls_or)
    return cls.build_snapshot(
        inp,
        confirmed_reservations=confirmed,
        committed_occupied_cells=occupied,
    )


def commit_best_genome(
    genome: Genome,
    candidate_pool: Sequence[BundleCandidate],
    optimization_input: OptimizationInput,
    route_domain_builder: RouteDomainSnapshotBuilder | type[RouteDomainSnapshotBuilder],
    recovery_budget: RecoveryBudget | None = None,
    *,
    probe_config: CandidateGenerationConfig | None = None,
    replay_recorder: OptimizationReplaySink | None = None,
) -> IncrementalCommitResult:
    """Incrementally confirm candidates in ``Gene.commit_order`` with fresh route probes."""

    cfg = probe_config or _DEFAULT_PROBE_CFG
    pairs = genome_commit_candidates(genome, candidate_pool)

    reservations: list[RouteReservation] = []
    placements: list[CommittedPlacement] = []
    results: list[CandidateCommitResult] = []
    committed_occ: set[Coord] = set()
    confirmed_tuple: tuple[RouteReservation, ...] = ()
    ordinal = 0
    probe_attempts = 0

    for _gene, cand in pairs:
        if recovery_budget is not None and probe_attempts >= recovery_budget.max_reroute_attempts:
            emit_route_commit_attempted(
                replay_recorder,
                candidate_id=cand.candidate_id,
                transport_kind=cand.transport_kind,
            )
            emit_route_rolled_back(
                replay_recorder,
                candidate_id=cand.candidate_id,
                transport_kind=cand.transport_kind,
                commit_conflict_reason=CommitConflictReason.TRUNK_DEADLOCK,
            )
            results.append(
                CandidateCommitResult(
                    candidate_id=cand.candidate_id,
                    commit_state=PlacementCommitState.ROLLED_BACK,
                    conflict_reason=CommitConflictReason.TRUNK_DEADLOCK,
                    route_reservation_id=None,
                    route_probe_result=_budget_probe_failure(),
                    message="recovery_budget.max_reroute_attempts exceeded",
                )
            )
            continue

        emit_route_commit_attempted(
            replay_recorder,
            candidate_id=cand.candidate_id,
            transport_kind=cand.transport_kind,
        )
        probe_attempts += 1
        route_domain = _invoke_build_commit(
            route_domain_builder,
            optimization_input,
            confirmed_tuple,
            frozenset(committed_occ),
        )
        occupied_overlay = frozenset(committed_occ | cand.occupied_cells)
        probe_inp = RouteProbeInput(
            start=cand.output_stub,
            goals=optimization_input.route_goals,
            route_domain=route_domain,
            topology_graph=optimization_input.topology_graph,
            max_expansions=cfg.route_probe_max_expansions,
            transport_kind=cand.transport_kind,
            goal_priority_weight=cfg.route_probe_goal_priority_weight,
            wall_clock_deadline_perf=cfg.wall_clock_deadline_perf,
        )
        probe_res = run_route_probe(probe_inp, occupied_cells=occupied_overlay)

        if not _probe_connected(probe_res):
            emit_route_rolled_back(
                replay_recorder,
                candidate_id=cand.candidate_id,
                transport_kind=cand.transport_kind,
                commit_conflict_reason=CommitConflictReason.ROUTE_PROBE_FAILED,
            )
            results.append(
                CandidateCommitResult(
                    candidate_id=cand.candidate_id,
                    commit_state=PlacementCommitState.ROLLED_BACK,
                    conflict_reason=CommitConflictReason.ROUTE_PROBE_FAILED,
                    route_reservation_id=None,
                    route_probe_result=probe_res,
                    message="route_probe_failed",
                )
            )
            continue

        path = probe_res.path
        reserved_cells = frozenset(path)
        reached_goal = probe_res.reached_goal
        goal_priority = probe_res.goal_priority
        if reached_goal is None or goal_priority is None:
            emit_route_rolled_back(
                replay_recorder,
                candidate_id=cand.candidate_id,
                transport_kind=cand.transport_kind,
                commit_conflict_reason=CommitConflictReason.ROUTE_PROBE_FAILED,
            )
            results.append(
                CandidateCommitResult(
                    candidate_id=cand.candidate_id,
                    commit_state=PlacementCommitState.ROLLED_BACK,
                    conflict_reason=CommitConflictReason.ROUTE_PROBE_FAILED,
                    route_reservation_id=None,
                    route_probe_result=probe_res,
                    message="route_probe_incomplete",
                )
            )
            continue

        conflict = _path_conflict_reason(
            inp=optimization_input,
            cand=cand,
            path=path,
            route_domain=route_domain,
            committed_occupied=frozenset(committed_occ),
            confirmed_reservations=confirmed_tuple,
        )
        if conflict is not None:
            emit_route_rolled_back(
                replay_recorder,
                candidate_id=cand.candidate_id,
                transport_kind=cand.transport_kind,
                commit_conflict_reason=conflict,
            )
            results.append(
                CandidateCommitResult(
                    candidate_id=cand.candidate_id,
                    commit_state=PlacementCommitState.ROLLED_BACK,
                    conflict_reason=conflict,
                    route_reservation_id=None,
                    route_probe_result=probe_res,
                    message=conflict.value,
                )
            )
            continue

        reservation_id = f"{cand.candidate_id}:route:{ordinal}"
        domain_before = route_domain
        next_occ_frozen = frozenset(committed_occ | cand.occupied_cells)

        temp_res = RouteReservation(
            reservation_id=reservation_id,
            candidate_id=cand.candidate_id,
            transport_kind=cand.transport_kind,
            path=path,
            reserved_cells=reserved_cells,
            cost=probe_res.cost,
            reached_goal=reached_goal,
            goal_priority=goal_priority,
            reservation_state=ReservationState.CONFIRMED,
            domain_cell_transitions=(),
        )
        domain_after = _invoke_build_commit(
            route_domain_builder,
            optimization_input,
            confirmed_tuple + (temp_res,),
            next_occ_frozen,
        )
        transitions = _domain_diff_route_classes(domain_before, domain_after)

        confirmed_res = RouteReservation(
            reservation_id=reservation_id,
            candidate_id=cand.candidate_id,
            transport_kind=cand.transport_kind,
            path=path,
            reserved_cells=reserved_cells,
            cost=probe_res.cost,
            reached_goal=reached_goal,
            goal_priority=goal_priority,
            reservation_state=ReservationState.CONFIRMED,
            domain_cell_transitions=transitions,
        )

        reservations.append(confirmed_res)
        placements.append(
            CommittedPlacement(
                candidate_id=cand.candidate_id,
                occupied_cells=cand.occupied_cells,
                transport_kind=cand.transport_kind,
                route_reservation_id=reservation_id,
            )
        )
        emit_route_committed(
            replay_recorder,
            candidate_id=cand.candidate_id,
            reservation=confirmed_res,
        )
        committed_occ.update(cand.occupied_cells)
        confirmed_tuple = tuple(reservations)
        ordinal += 1

        results.append(
            CandidateCommitResult(
                candidate_id=cand.candidate_id,
                commit_state=PlacementCommitState.CONFIRMED,
                conflict_reason=None,
                route_reservation_id=reservation_id,
                route_probe_result=probe_res,
                message="confirmed",
            )
        )

    final_domain = _invoke_build_commit(
        route_domain_builder,
        optimization_input,
        confirmed_tuple,
        frozenset(committed_occ),
    )
    n_ok = sum(1 for r in results if r.commit_state is PlacementCommitState.CONFIRMED)
    n_bad = sum(1 for r in results if r.commit_state is PlacementCommitState.ROLLED_BACK)
    return IncrementalCommitResult(
        committed_placements=tuple(placements),
        route_reservations=tuple(reservations),
        candidate_results=tuple(results),
        final_route_domain=final_domain,
        confirmed_candidate_count=n_ok,
        rolled_back_candidate_count=n_bad,
    )
