"""Phase H — candidate pool DTOs and normal-candidate factory (PR3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import (
    CandidateRejectReason,
    Direction,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.gene_projection import ProjectedGenePlacement
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult
from django_apps.asteroid_lab.optimization.timing_metrics import CandidateGenerationTiming


class ExtractorPlacementPolicy(StrEnum):
    """How candidate anchors are chosen (v0: rim-only enumeration)."""

    RIM_ONLY = "rim_only"


@dataclass(frozen=True, slots=True)
class CandidateGenerationConfig:
    extractor_policy: ExtractorPlacementPolicy
    allow_diagnostic_unreachable: bool
    max_candidates: int | None
    route_probe_max_expansions: int
    transport_kinds: frozenset[TransportKind]
    route_probe_goal_priority_weight: int = 10
    probe_budget_factor: int = 4


@dataclass(frozen=True, slots=True)
class GeneCandidate:
    candidate_id: str
    gene_id: str
    topology_signature: str
    extractor: Coord
    extensions: tuple[Coord, ...]
    occupied_cells: frozenset[Coord]
    route_probe_start: Coord
    fixed_output_transport: Coord
    output_dir: Direction
    transport_kind: TransportKind
    base_throughput: int
    base_score: float
    route_probe_result: RouteProbeResult


@dataclass(frozen=True, slots=True)
class RejectedGeneCandidate:
    attempted_gene_id: str
    extractor: Coord | None
    rejection_reason: CandidateRejectReason
    route_probe_result: RouteProbeResult | None


@dataclass(frozen=True, slots=True)
class GenerationDiagnostics:
    """Gate C supply-chain counters (summary/replay only; does not affect pool)."""

    rim_cell_count: int = 0
    reachable_anchors_after_prefilter_count: int = 0
    truncated_by_max_candidates_count: int = 0
    normal_pool_variants_per_anchor_max: int = 0
    unique_anchors_after_probe_budget_count: int = 0
    anchors_dropped_by_probe_budget_count: int = 0
    probe_budget_floor_reserved_count: int = 0
    probe_budget_fill_count: int = 0
    unique_anchors_after_dedupe_count: int = 0
    anchor_preserved_by_truncation_count: int = 0
    anchor_dropped_by_truncation_count: int = 0


@dataclass(frozen=True, slots=True)
class CandidateGenerationResult:
    normal_candidates: tuple[GeneCandidate, ...]
    rejected_candidates: tuple[RejectedGeneCandidate, ...]
    timing: CandidateGenerationTiming | None = None
    projected_candidate_count_before_probe: int = 0
    pre_dedupe_normal_count: int = 0
    deduped_candidate_count: int = 0
    generation_diagnostics: GenerationDiagnostics = GenerationDiagnostics()


def make_candidate_id(
    *,
    gene_id: str,
    anchor: Coord,
    rotation: Direction,
    transport_kind: TransportKind,
) -> str:
    ax, ay = anchor
    return f"{gene_id}:{ax},{ay}:{rotation.value}:{transport_kind.value}"


def make_topology_signature(
    *,
    gene: GeneTemplate,
    projected: ProjectedGenePlacement,
    rotation: Direction,
    transport_kind: TransportKind,
) -> str:
    occupied = ",".join(f"{x},{y}" for x, y in sorted(projected.occupied_cells))
    rps = projected.route_probe_start
    fot = projected.fixed_output_transport
    return (
        f"gene={gene.gene_id}"
        f"|rot={rotation.value}"
        f"|tk={transport_kind.value}"
        f"|tp={gene.throughput_factor}"
        f"|out={projected.output_dir.value}"
        f"|occ={occupied}"
        f"|rps={rps[0]},{rps[1]}"
        f"|fot={fot[0]},{fot[1]}"
    )


def build_normal_gene_candidate(
    *,
    gene: GeneTemplate,
    projected: ProjectedGenePlacement,
    rotation: Direction,
    transport_kind: TransportKind,
    route_probe_result: RouteProbeResult,
) -> GeneCandidate:
    """Factory-only construction; asserts reachable probe contract."""

    if not route_probe_result.reachable:
        msg = "normal candidate requires reachable route_probe_result"
        raise ValueError(msg)
    if route_probe_result.reached_goal is None:
        msg = "normal candidate requires reached_goal"
        raise ValueError(msg)

    candidate_id = make_candidate_id(
        gene_id=gene.gene_id,
        anchor=projected.extractor,
        rotation=rotation,
        transport_kind=transport_kind,
    )
    topology_signature = make_topology_signature(
        gene=gene,
        projected=projected,
        rotation=rotation,
        transport_kind=transport_kind,
    )
    base_throughput = gene.throughput_factor
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id=gene.gene_id,
        topology_signature=topology_signature,
        extractor=projected.extractor,
        extensions=projected.extensions,
        occupied_cells=projected.occupied_cells,
        route_probe_start=projected.route_probe_start,
        fixed_output_transport=projected.fixed_output_transport,
        output_dir=projected.output_dir,
        transport_kind=transport_kind,
        base_throughput=base_throughput,
        base_score=float(base_throughput),
        route_probe_result=route_probe_result,
    )
