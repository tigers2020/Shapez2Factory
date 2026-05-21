"""Phase H — enumerate projected genes, probe routes, build reachable-only pool (PR3)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationConfig,
    CandidateGenerationResult,
    ExtractorPlacementPolicy,
    GeneCandidate,
    GenerationDiagnostics,
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


def _candidate_rank_key(candidate: GeneCandidate) -> tuple[float, int, str]:
    return (
        -candidate.base_score,
        candidate.route_probe_result.cost,
        candidate.candidate_id,
    )


def _truncate_with_anchor_floor(
    candidates: tuple[GeneCandidate, ...],
    max_candidates: int,
) -> tuple[GeneCandidate, ...]:
    """Keep one best candidate per extractor, then fill remaining slots by global rank."""

    if len(candidates) <= max_candidates:
        return candidates

    ranked = sorted(candidates, key=_candidate_rank_key)
    best_per_anchor: dict[Coord, GeneCandidate] = {}
    for candidate in ranked:
        if candidate.extractor not in best_per_anchor:
            best_per_anchor[candidate.extractor] = candidate

    floor = sorted(best_per_anchor.values(), key=_candidate_rank_key)
    if len(floor) >= max_candidates:
        return tuple(floor[:max_candidates])

    chosen_ids = {c.candidate_id for c in floor}
    result: list[GeneCandidate] = list(floor)
    for candidate in ranked:
        if len(result) >= max_candidates:
            break
        if candidate.candidate_id in chosen_ids:
            continue
        result.append(candidate)
        chosen_ids.add(candidate.candidate_id)
    return tuple(result)


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


def _variants_per_anchor_max(candidates: tuple[GeneCandidate, ...]) -> int:
    per_anchor: dict[Coord, int] = {}
    for candidate in candidates:
        per_anchor[candidate.extractor] = per_anchor.get(candidate.extractor, 0) + 1
    return max(per_anchor.values(), default=0)


def _winner_probe_sort_key(
    winner: _ProbeWinner,
    base_dist_maps: dict[TransportKind, dict[Coord, int]],
) -> tuple[int, str]:
    return (_winner_base_distance(winner, base_dist_maps), winner.candidate_id)


@dataclass(frozen=True, slots=True)
class _ProbeCapResult:
    winners: tuple[_ProbeWinner, ...]
    floor_reserved_count: int
    fill_count: int


def _cap_probe_winners_with_anchor_floor(
    winners: tuple[_ProbeWinner, ...],
    probe_budget: int,
    base_dist_maps: dict[TransportKind, dict[Coord, int]],
) -> _ProbeCapResult:
    """Reserve one best winner per extractor, then fill remaining probe slots by distance rank."""

    unique_anchors = len({w.projected.extractor for w in winners})
    if len(winners) <= probe_budget:
        return _ProbeCapResult(
            winners=winners,
            floor_reserved_count=unique_anchors,
            fill_count=max(0, len(winners) - unique_anchors),
        )

    best_per_anchor: dict[Coord, _ProbeWinner] = {}
    for winner in winners:
        extractor = winner.projected.extractor
        if extractor not in best_per_anchor:
            best_per_anchor[extractor] = winner

    floor = sorted(
        best_per_anchor.values(),
        key=lambda w: _winner_probe_sort_key(w, base_dist_maps),
    )
    if len(floor) >= probe_budget:
        capped = tuple(floor[:probe_budget])
        return _ProbeCapResult(
            winners=capped,
            floor_reserved_count=probe_budget,
            fill_count=0,
        )

    chosen_ids = {w.candidate_id for w in floor}
    result: list[_ProbeWinner] = list(floor)
    floor_in_result = len(result)
    for winner in winners:
        if len(result) >= probe_budget:
            break
        if winner.candidate_id in chosen_ids:
            continue
        result.append(winner)
        chosen_ids.add(winner.candidate_id)

    return _ProbeCapResult(
        winners=tuple(result),
        floor_reserved_count=floor_in_result,
        fill_count=len(result) - floor_in_result,
    )


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

    reachable_anchors_after_prefilter_count = len(
        {w.projected.extractor for w in reachable_winners}
    )

    sorted_winners = _sort_winners_for_probe(
        tuple(reachable_winners),
        base_dist_maps,
    )
    probe_budget = _probe_budget(config)
    if probe_budget is not None:
        cap_result = _cap_probe_winners_with_anchor_floor(
            sorted_winners,
            probe_budget,
            base_dist_maps,
        )
        sorted_winners = cap_result.winners
        probe_cap_floor_reserved = cap_result.floor_reserved_count
        probe_cap_fill = cap_result.fill_count
    else:
        unique_probe_anchors = len({w.projected.extractor for w in sorted_winners})
        probe_cap_floor_reserved = unique_probe_anchors
        probe_cap_fill = max(0, len(sorted_winners) - unique_probe_anchors)

    unique_anchors_after_probe_budget_count = len({w.projected.extractor for w in sorted_winners})
    anchors_dropped_by_probe_budget_count = max(
        0,
        reachable_anchors_after_prefilter_count - unique_anchors_after_probe_budget_count,
    )

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
    pre_truncation_count = len(deduped)
    anchors_after_dedupe = len({c.extractor for c in deduped})
    if config.max_candidates is not None:
        deduped = _truncate_with_anchor_floor(deduped, config.max_candidates)
    truncated_by_max_candidates_count = max(0, pre_truncation_count - len(deduped))
    anchors_in_pool = len({c.extractor for c in deduped})
    anchor_dropped = max(0, anchors_after_dedupe - anchors_in_pool)

    generation_diagnostics = GenerationDiagnostics(
        rim_cell_count=len(inp.rim_cells),
        reachable_anchors_after_prefilter_count=reachable_anchors_after_prefilter_count,
        truncated_by_max_candidates_count=truncated_by_max_candidates_count,
        normal_pool_variants_per_anchor_max=_variants_per_anchor_max(deduped),
        unique_anchors_after_probe_budget_count=unique_anchors_after_probe_budget_count,
        anchors_dropped_by_probe_budget_count=anchors_dropped_by_probe_budget_count,
        probe_budget_floor_reserved_count=probe_cap_floor_reserved,
        probe_budget_fill_count=probe_cap_fill,
        unique_anchors_after_dedupe_count=anchors_after_dedupe,
        anchor_preserved_by_truncation_count=anchors_in_pool,
        anchor_dropped_by_truncation_count=anchor_dropped,
    )

    return CandidateGenerationResult(
        normal_candidates=deduped,
        rejected_candidates=tuple(rejected),
        timing=timing,
        projected_candidate_count_before_probe=projected_candidate_count_before_probe,
        pre_dedupe_normal_count=pre_dedupe_normal_count,
        deduped_candidate_count=deduped_candidate_count,
        generation_diagnostics=generation_diagnostics,
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
