"""Phase H — enumerate projected genes, probe routes, build reachable-only pool (PR3)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationConfig,
    CandidateGenerationResult,
    ExtractorPlacementPolicy,
    GeneCandidate,
    RejectedGeneCandidate,
    build_normal_gene_candidate,
)
from django_apps.asteroid_lab.optimization.candidate_equivalence import (
    dedupe_gene_candidates,
)
from django_apps.asteroid_lab.optimization.candidate_geometry import (
    validate_projected_gene_geometry,
)
from django_apps.asteroid_lab.optimization.enums import (
    CandidateRejectReason,
    Direction,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.gene_projection import project_gene_placement
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.route_probe import (
    RouteProbeInput,
    build_route_domain_for_projected_gene_probe,
    run_route_probe,
)

_ROTATION_ORDER: tuple[Direction, ...] = (
    Direction.N,
    Direction.E,
    Direction.S,
    Direction.W,
)


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


def generate_gene_candidates(
    inp: OptimizationInput,
    gene_templates: tuple[GeneTemplate, ...],
    config: CandidateGenerationConfig,
) -> CandidateGenerationResult:
    """Build normal/rejected pools without committing placements."""

    if config.extractor_policy is not ExtractorPlacementPolicy.RIM_ONLY:
        msg = f"unsupported extractor_policy: {config.extractor_policy!r}"
        raise ValueError(msg)

    normal: list[GeneCandidate] = []
    rejected: list[RejectedGeneCandidate] = []

    sorted_rim = sorted(inp.rim_cells, key=lambda c: (c[0], c[1]))
    sorted_genes = sorted(gene_templates, key=lambda g: g.gene_id)
    sorted_transport = sorted(config.transport_kinds, key=lambda k: k.value)

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

                domain = build_route_domain_for_projected_gene_probe(inp, projected)
                for transport_kind in sorted_transport:
                    probe = RouteProbeInput(
                        start=projected.route_probe_start,
                        goals=inp.route_goals,
                        route_domain=domain,
                        topology_graph=inp.topology_graph,
                        max_expansions=config.route_probe_max_expansions,
                        transport_kind=transport_kind,
                        goal_priority_weight=config.route_probe_goal_priority_weight,
                    )
                    probe_result = run_route_probe(probe)
                    if not probe_result.reachable or probe_result.reached_goal is None:
                        rejected.append(
                            RejectedGeneCandidate(
                                attempted_gene_id=gene.gene_id,
                                extractor=projected.extractor,
                                rejection_reason=CandidateRejectReason.ROUTE_PROBE_UNREACHABLE,
                                route_probe_result=probe_result,
                            )
                        )
                        continue

                    normal.append(
                        build_normal_gene_candidate(
                            gene=gene,
                            projected=projected,
                            rotation=rotation,
                            transport_kind=transport_kind,
                            route_probe_result=probe_result,
                        )
                    )

    deduped = dedupe_gene_candidates(tuple(normal))
    if config.max_candidates is not None:
        deduped = _truncate_normal_candidates(deduped, config.max_candidates)

    return CandidateGenerationResult(
        normal_candidates=deduped,
        rejected_candidates=tuple(rejected),
    )


def default_generation_config(
    *,
    max_candidates: int | None = None,
    route_probe_max_expansions: int = 500,
    transport_kinds: frozenset[TransportKind] | None = None,
) -> CandidateGenerationConfig:
    """v0 defaults for tests and orchestration stubs."""

    kinds = transport_kinds or frozenset({TransportKind.SHAPE_BELT})
    return CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=False,
        max_candidates=max_candidates,
        route_probe_max_expansions=route_probe_max_expansions,
        transport_kinds=kinds,
    )
