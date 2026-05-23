"""Generate bundle candidates with immediate route probe (RTTP Layer 2, PR-3)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    CandidateGenerationResult,
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    RejectedBundleCandidate,
)
from django_apps.asteroid_lab.optimization.candidates.pattern_library import (
    BundlePattern,
    build_pattern_library,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def _anchor_cells(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    policy: ExtractorPlacementPolicy,
) -> tuple[Coord, ...]:
    if policy is ExtractorPlacementPolicy.RIM_ONLY:
        cells = inp.rim_cells
    elif policy is ExtractorPlacementPolicy.INTERIOR_AND_RIM:
        cells = inp.rim_cells | skeleton.inner_cells
    else:
        msg = f"unsupported extractor policy: {policy!r}"
        raise ValueError(msg)
    return tuple(sorted(cells))


def _goal_coords(inp: OptimizationInput) -> frozenset[Coord]:
    return frozenset(
        goal.coord
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
    )


def _translate_offset(anchor: Coord, offset: Coord) -> Coord:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _project_pattern(anchor: Coord, pattern: BundlePattern) -> tuple[frozenset[Coord], Coord]:
    occupied = frozenset(_translate_offset(anchor, offset) for offset in pattern.occupied_offsets)
    output_stub = _translate_offset(anchor, pattern.output_stub_offset)
    return occupied, output_stub


def _validate_geometry(
    inp: OptimizationInput,
    pattern: BundlePattern,
    occupied: frozenset[Coord],
    output_stub: Coord,
) -> CandidateRejectReason | None:
    if len(occupied) != len(pattern.occupied_offsets):
        return CandidateRejectReason.OVERLAP
    if not occupied.issubset(inp.mineable_cells):
        return CandidateRejectReason.GEOMETRY_INVALID
    if output_stub in occupied:
        return CandidateRejectReason.GEOMETRY_INVALID
    return None


def _dedupe_signature(
    occupied: frozenset[Coord],
    output_stub: Coord,
    output_dir: str,
    throughput_factor: int,
) -> tuple[tuple[Coord, ...], Coord, str, int]:
    return (tuple(sorted(occupied)), output_stub, output_dir, throughput_factor)


def _make_candidate_id(
    anchor: Coord,
    pattern: BundlePattern,
    transport_kind_value: str,
) -> str:
    return f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:{transport_kind_value}"


def generate_candidates(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    max_candidates: int | None = None,
    max_expansions: int = 500,
) -> CandidateGenerationResult:
    """Enumerate anchor × pattern placements; probe before normal pool admission."""

    domain = build_route_domain_from_skeleton(skeleton, inp)
    goals = _goal_coords(inp)
    patterns = build_pattern_library()
    anchors = _anchor_cells(inp, skeleton, policy)

    normal_by_signature: dict[
        tuple[tuple[Coord, ...], Coord, str, int],
        BundleCandidate,
    ] = {}
    rejected: list[RejectedBundleCandidate] = []

    for anchor in anchors:
        for pattern in patterns:
            occupied, output_stub = _project_pattern(anchor, pattern)
            candidate_id = _make_candidate_id(anchor, pattern, inp.transport_kind.value)

            geometry_reason = _validate_geometry(inp, pattern, occupied, output_stub)
            if geometry_reason is not None:
                rejected.append(
                    RejectedBundleCandidate(
                        candidate_id=candidate_id,
                        anchor_coord=anchor,
                        pattern_id=pattern.pattern_id,
                        rejection_reason=geometry_reason,
                        route_probe_cost=None,
                    )
                )
                continue

            probe = probe_route(
                domain,
                output_stub,
                goals,
                max_expansions=max_expansions,
            )
            if not probe.reachable:
                rejected.append(
                    RejectedBundleCandidate(
                        candidate_id=candidate_id,
                        anchor_coord=anchor,
                        pattern_id=pattern.pattern_id,
                        rejection_reason=CandidateRejectReason.NOT_REACHABLE,
                        route_probe_cost=probe.cost,
                    )
                )
                continue

            candidate = BundleCandidate(
                candidate_id=candidate_id,
                anchor_coord=anchor,
                pattern=pattern,
                occupied_cells=occupied,
                output_stub=output_stub,
                output_dir=pattern.output_dir,
                transport_kind=inp.transport_kind,
                throughput_factor=pattern.throughput_factor,
                route_probe_cost=probe.cost,
                reachable=True,
            )
            signature = _dedupe_signature(
                occupied,
                output_stub,
                pattern.output_dir,
                pattern.throughput_factor,
            )
            existing = normal_by_signature.get(signature)
            if existing is None or candidate.candidate_id < existing.candidate_id:
                normal_by_signature[signature] = candidate

    normal = tuple(sorted(normal_by_signature.values(), key=lambda item: item.candidate_id))
    if max_candidates is not None and len(normal) > max_candidates:
        normal = normal[:max_candidates]

    return CandidateGenerationResult(
        normal_candidates=normal,
        rejected_candidates=tuple(rejected),
    )


__all__ = ["generate_candidates"]
