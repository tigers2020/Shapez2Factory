"""Generate bundle candidates with immediate route probe (RTTP Layer 2, PR-3)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_candidate_placements import (
    build_catalog_placement_specs,
)
from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.contracts.catalog_candidate import CatalogPlacementSpec
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementRef,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    CandidateGenerationResult,
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RejectedBundleCandidate,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
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


def _translate_offset(anchor: Coord, offset: Coord) -> Coord:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _bundle_pattern_from_spec(spec: CatalogPlacementSpec) -> BundlePattern:
    return BundlePattern(
        pattern_id=spec.pattern_id,
        extension_count=len(spec.extension_offsets),
        occupied_offsets=spec.occupied_offsets,
        extractor_offset=spec.extractor_offset,
        extension_offsets=spec.extension_offsets,
        output_dir=spec.output_dir,
        fixed_output_transport_offset=spec.fixed_output_transport_offset,
        output_stub_offset=spec.output_stub_offset,
        throughput_factor=spec.throughput_factor,
        topology_kind=spec.topology_kind,
    )


def _project_spec(anchor: Coord, spec: CatalogPlacementSpec) -> tuple[frozenset[Coord], Coord]:
    occupied = frozenset(_translate_offset(anchor, offset) for offset in spec.occupied_offsets)
    output_stub = _translate_offset(anchor, spec.output_stub_offset)
    return occupied, output_stub


def _policy_requires_outside_mineable(policy: FixedOutputTransportPolicy) -> bool:
    return policy in (
        FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
        FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
    )


def _validate_geometry(
    inp: OptimizationInput,
    spec: CatalogPlacementSpec,
    anchor: Coord,
    occupied: frozenset[Coord],
    output_stub: Coord,
    *,
    fot_abs: Coord,
    policy: FixedOutputTransportPolicy,
) -> CandidateRejectReason | None:
    if spec.extractor_offset != (0, 0):
        return CandidateRejectReason.GEOMETRY_INVALID
    if len(occupied) != len(spec.occupied_offsets):
        return CandidateRejectReason.OVERLAP
    if not occupied.issubset(inp.mineable_cells):
        return CandidateRejectReason.GEOMETRY_INVALID

    stub_abs = _translate_offset(anchor, spec.output_stub_offset)
    if fot_abs in occupied:
        return CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED
    if fot_abs in inp.blocked_incompatible_transport_cells:
        return CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED
    if _policy_requires_outside_mineable(policy) and fot_abs in inp.mineable_cells:
        return CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
    if stub_abs in occupied:
        return CandidateRejectReason.ROUTE_PROBE_START_IN_OCCUPIED
    if output_stub != stub_abs:
        return CandidateRejectReason.GEOMETRY_INVALID

    unit = cardinal_unit_vector(CardinalDirection(spec.output_dir))
    axis_local = (
        spec.extractor_offset[0] + unit[0],
        spec.extractor_offset[1] + unit[1],
    )
    if axis_local in spec.extension_offsets:
        return CandidateRejectReason.EXTENSION_ON_OUTPUT_AXIS
    return None


def _dedupe_signature(
    occupied: frozenset[Coord],
    output_stub: Coord,
    output_dir: str,
    throughput_factor: int,
) -> tuple[tuple[Coord, ...], Coord, str, int]:
    return (tuple(sorted(occupied)), output_stub, output_dir, throughput_factor)


def _make_candidate_id(anchor: Coord, pattern_id: str, transport_kind_value: str) -> str:
    return f"{anchor[0]},{anchor[1]}:{pattern_id}:{transport_kind_value}"


def generate_candidates(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    fixed_output_transport_policy: FixedOutputTransportPolicy = (
        FixedOutputTransportPolicy.ALLOW
    ),
    max_candidates: int | None = None,
    max_expansions: int = 500,
) -> CandidateGenerationResult:
    """Enumerate anchor × catalog placement specs; probe before normal pool admission."""

    if inp.catalog_slice is None:
        return CandidateGenerationResult(normal_candidates=(), rejected_candidates=())

    domain = build_route_domain_from_skeleton(skeleton, inp)
    goals = probe_goal_coords(inp, skeleton)
    specs = build_catalog_placement_specs(inp.catalog_slice, transport_kind=inp.transport_kind)
    anchors = _anchor_cells(inp, skeleton, policy)

    normal_by_signature: dict[
        tuple[tuple[Coord, ...], Coord, str, int],
        BundleCandidate,
    ] = {}
    rejected: list[RejectedBundleCandidate] = []

    for anchor in anchors:
        for spec in specs:
            pattern = _bundle_pattern_from_spec(spec)
            occupied, output_stub = _project_spec(anchor, spec)
            candidate_id = _make_candidate_id(anchor, spec.pattern_id, inp.transport_kind.value)
            ref = CatalogPlacementRef(spec.canonical_id, anchor, spec.rotation)

            fot_abs = _translate_offset(anchor, spec.fixed_output_transport_offset)
            geometry_reason = _validate_geometry(
                inp,
                spec,
                anchor,
                occupied,
                output_stub,
                fot_abs=fot_abs,
                policy=fixed_output_transport_policy,
            )
            if geometry_reason is not None:
                rejected.append(
                    RejectedBundleCandidate(
                        candidate_id=candidate_id,
                        anchor_coord=anchor,
                        pattern_id=spec.pattern_id,
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
                        pattern_id=spec.pattern_id,
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
                output_dir=spec.output_dir,
                transport_kind=inp.transport_kind,
                throughput_factor=spec.throughput_factor,
                route_probe_cost=probe.cost,
                reachable=True,
                catalog_placement_ref=ref,
            )
            signature = _dedupe_signature(
                occupied,
                output_stub,
                spec.output_dir,
                spec.throughput_factor,
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
