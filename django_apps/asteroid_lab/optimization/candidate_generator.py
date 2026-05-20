"""Phase H — enumerate projected genes, probe routes, build reachable-only pool (PR3)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationConfig,
    CandidateGenerationResult,
    ExtractorPlacementPolicy,
    GeneCandidate,
    RejectedGeneCandidate,
    build_normal_gene_candidate,
    make_candidate_id,
)
from django_apps.asteroid_lab.optimization.candidate_equivalence import (
    CandidateEquivalenceKey,
    dedupe_gene_candidates,
    equivalence_key_for_attempt,
)
from django_apps.asteroid_lab.optimization.candidate_geometry import (
    validate_projected_gene_geometry,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import (
    CandidateRejectReason,
    Direction,
    RouteProbeFailureReason,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.gene_projection import (
    ProjectedGenePlacement,
    project_gene_placement,
)
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.route_distance_cache import (
    _build_reverse_distance_map,
)
from django_apps.asteroid_lab.optimization.route_domain import RouteDomainSnapshotBuilder
from django_apps.asteroid_lab.optimization.route_probe import (
    RouteProbeInput,
    RouteProbeResult,
    build_route_domain_for_projected_gene_probe,
    run_route_probe,
)
from django_apps.asteroid_lab.optimization.timing_metrics import CandidateGenerationTiming

_ROTATION_ORDER: tuple[Direction, ...] = (
    Direction.N,
    Direction.E,
    Direction.S,
    Direction.W,
)


@dataclass(frozen=True, slots=True)
class _ProbeWinner:
    gene: GeneTemplate
    projected: ProjectedGenePlacement
    rotation: Direction
    transport_kind: TransportKind
    candidate_id: str
    equivalence_key: CandidateEquivalenceKey


def _truncate_normal_candidates(
    candidates: tuple[GeneCandidate, ...],
    max_candidates: int,
) -> tuple[GeneCandidate, ...]:
    ranked = sorted(
        candidates,
        key=lambda c: (
            -c.base_score,
            c.route_probe_result.cost,
            c.candidate_id,
        ),
    )
    return tuple(ranked[:max_candidates])


def _unreachable_prefilter_result() -> RouteProbeResult:
    return RouteProbeResult(
        reachable=False,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=None,
        goal_priority=None,
        failure_reason=RouteProbeFailureReason.EXHAUSTED,
    )


def _probe_budget(config: CandidateGenerationConfig) -> int | None:
    if config.max_candidates is None:
        return None
    return config.max_candidates * config.probe_budget_factor


def _winner_base_distance(
    winner: _ProbeWinner,
    base_dist_maps: dict[TransportKind, dict[Coord, int]],
) -> int:
    dist_map = base_dist_maps[winner.transport_kind]
    return dist_map.get(winner.projected.route_probe_start, 2**31)


def _sort_winners_for_probe(
    winners: tuple[_ProbeWinner, ...],
    base_dist_maps: dict[TransportKind, dict[Coord, int]],
) -> tuple[_ProbeWinner, ...]:
    return tuple(
        sorted(
            winners,
            key=lambda w: (_winner_base_distance(w, base_dist_maps), w.candidate_id),
        )
    )


def _cap_probe_winners(
    winners: tuple[_ProbeWinner, ...],
    probe_budget: int,
) -> tuple[_ProbeWinner, ...]:
    if len(winners) <= probe_budget:
        return winners
    return winners[:probe_budget]


def generate_gene_candidates(
    inp: OptimizationInput,
    gene_templates: tuple[GeneTemplate, ...],
    config: CandidateGenerationConfig,
) -> CandidateGenerationResult:
    """Build normal/rejected pools without committing placements."""

    if config.extractor_policy is not ExtractorPlacementPolicy.RIM_ONLY:
        msg = f"unsupported extractor_policy: {config.extractor_policy!r}"
        raise ValueError(msg)

    gen_start = time.perf_counter()
    timing = CandidateGenerationTiming()

    normal: list[GeneCandidate] = []
    rejected: list[RejectedGeneCandidate] = []

    sorted_rim = sorted(inp.rim_cells, key=lambda c: (c[0], c[1]))
    sorted_genes = sorted(gene_templates, key=lambda g: g.gene_id)
    sorted_transport = sorted(config.transport_kinds, key=lambda k: k.value)

    winners_by_key: dict[CandidateEquivalenceKey, _ProbeWinner] = {}
    for anchor in sorted_rim:
        for gene in sorted_genes:
            for rotation in _ROTATION_ORDER:
                projected = project_gene_placement(
                    anchor=anchor,
                    rotation=rotation,
                    gene=gene,
                )
                geo = validate_projected_gene_geometry(inp, projected)
                if not geo.valid:
                    rejected.append(
                        RejectedGeneCandidate(
                            attempted_gene_id=gene.gene_id,
                            extractor=projected.extractor,
                            rejection_reason=geo.reject_reason
                            or CandidateRejectReason.EXTRACTOR_NOT_RIM,
                            route_probe_result=None,
                        )
                    )
                    continue

                for transport_kind in sorted_transport:
                    key = equivalence_key_for_attempt(
                        gene=gene,
                        projected=projected,
                        rotation=rotation,
                        transport_kind=transport_kind,
                    )
                    candidate_id = make_candidate_id(
                        gene_id=gene.gene_id,
                        anchor=projected.extractor,
                        rotation=rotation,
                        transport_kind=transport_kind,
                    )
                    existing = winners_by_key.get(key)
                    if existing is None or candidate_id < existing.candidate_id:
                        winners_by_key[key] = _ProbeWinner(
                            gene=gene,
                            projected=projected,
                            rotation=rotation,
                            transport_kind=transport_kind,
                            candidate_id=candidate_id,
                            equivalence_key=key,
                        )

    base_seed = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    base_dist_maps: dict[TransportKind, dict[Coord, int]] = {}
    for transport_kind in sorted_transport:
        base_dist_maps[transport_kind] = _build_reverse_distance_map(
            base_seed,
            goals=inp.route_goals,
            transport_kind=transport_kind,
        )

    reachable_winners: list[_ProbeWinner] = []
    for winner in winners_by_key.values():
        if winner.projected.route_probe_start not in base_dist_maps[winner.transport_kind]:
            rejected.append(
                RejectedGeneCandidate(
                    attempted_gene_id=winner.gene.gene_id,
                    extractor=winner.projected.extractor,
                    rejection_reason=CandidateRejectReason.ROUTE_PROBE_UNREACHABLE,
                    route_probe_result=_unreachable_prefilter_result(),
                )
            )
            continue
        reachable_winners.append(winner)

    sorted_winners = _sort_winners_for_probe(
        tuple(reachable_winners),
        base_dist_maps,
    )
    probe_budget = _probe_budget(config)
    if probe_budget is not None:
        sorted_winners = _cap_probe_winners(sorted_winners, probe_budget)

    domain_by_blocked: dict[frozenset[Coord], dict] = {}
    for winner in sorted_winners:
        projected = winner.projected
        provisional = projected.occupied_cells | frozenset({projected.fixed_output_transport})
        domain = domain_by_blocked.get(provisional)
        if domain is None:
            dom_start = time.perf_counter()
            domain = build_route_domain_for_projected_gene_probe(inp, projected)
            timing.record_domain_build(elapsed_ms=(time.perf_counter() - dom_start) * 1000.0)
            domain_by_blocked[provisional] = domain

        start = projected.route_probe_start
        probe_start = time.perf_counter()
        probe_result = run_route_probe(
            RouteProbeInput(
                start=start,
                goals=inp.route_goals,
                route_domain=domain,
                topology_graph=inp.topology_graph,
                max_expansions=config.route_probe_max_expansions,
                transport_kind=winner.transport_kind,
                goal_priority_weight=config.route_probe_goal_priority_weight,
            )
        )
        timing.record_probe(
            elapsed_ms=(time.perf_counter() - probe_start) * 1000.0,
            expanded_nodes=probe_result.expanded_nodes,
        )

        if not probe_result.reachable or probe_result.reached_goal is None:
            rejected.append(
                RejectedGeneCandidate(
                    attempted_gene_id=winner.gene.gene_id,
                    extractor=projected.extractor,
                    rejection_reason=CandidateRejectReason.ROUTE_PROBE_UNREACHABLE,
                    route_probe_result=probe_result,
                )
            )
            continue

        normal.append(
            build_normal_gene_candidate(
                gene=winner.gene,
                projected=winner.projected,
                rotation=winner.rotation,
                transport_kind=winner.transport_kind,
                route_probe_result=probe_result,
            )
        )

    timing.finalize(total_ms=(time.perf_counter() - gen_start) * 1000.0)

    pre_dedupe_normal_count = len(normal)
    projected_candidate_count_before_probe = len(winners_by_key)
    deduped = dedupe_gene_candidates(tuple(normal))
    deduped_candidate_count = len(deduped)
    if config.max_candidates is not None:
        deduped = _truncate_normal_candidates(deduped, config.max_candidates)

    return CandidateGenerationResult(
        normal_candidates=deduped,
        rejected_candidates=tuple(rejected),
        timing=timing,
        projected_candidate_count_before_probe=projected_candidate_count_before_probe,
        pre_dedupe_normal_count=pre_dedupe_normal_count,
        deduped_candidate_count=deduped_candidate_count,
    )


def default_generation_config(
    *,
    max_candidates: int | None = 64,
    route_probe_max_expansions: int = 256,
    transport_kinds: frozenset[TransportKind] | None = None,
    probe_budget_factor: int = 4,
) -> CandidateGenerationConfig:
    """v0 defaults for tests and orchestration stubs."""

    kinds = transport_kinds or frozenset({TransportKind.SHAPE_BELT})
    return CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=False,
        max_candidates=max_candidates,
        route_probe_max_expansions=route_probe_max_expansions,
        transport_kinds=kinds,
        probe_budget_factor=probe_budget_factor,
    )
