"""Bundle candidate DTOs for RTTP Layer 2 (PR-3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementRef
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


class ExtractorPlacementPolicy(StrEnum):
    RIM_ONLY = "rim_only"
    INTERIOR_AND_RIM = "interior_and_rim"


class FixedOutputTransportPolicy(StrEnum):
    ALLOW = "allow"
    PENALIZE_FIELD_USAGE = "penalize_field_usage"
    OUTSIDE_MINEABLE = "outside_mineable"
    OUTWARD_FROM_RIM = "outward_from_rim"


class RouteProbeStartPolicy(StrEnum):
    OUTPUT_STUB_ONLY = "output_stub_only"
    PLATFORM_FALLBACK_WHEN_STUB_BLOCKED = "platform_fallback_when_stub_blocked"


class CandidateRejectReason(StrEnum):
    NOT_REACHABLE = "not_reachable"
    GEOMETRY_INVALID = "geometry_invalid"
    OVERLAP = "overlap"
    FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED = "fixed_output_transport_in_occupied"
    FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE = "fixed_output_transport_inside_mineable"
    FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED = "fixed_output_transport_kind_blocked"
    OUTPUT_DIR_NOT_OUTWARD_FROM_RIM = "output_dir_not_outward_from_rim"
    FIXED_OUTPUT_TRANSPORT_NOT_ON_ATTACH_SURFACE = (
        "fixed_output_transport_not_on_attach_surface"
    )
    FIXED_OUTPUT_TRANSPORT_NOT_IN_ROUTE_DOMAIN = "fixed_output_transport_not_in_route_domain"
    ROUTE_PROBE_START_BLOCKED = "route_probe_start_blocked"
    ROUTE_PROBE_START_IN_OCCUPIED = "route_probe_start_in_occupied"
    EXTENSION_ON_OUTPUT_AXIS = "extension_on_output_axis"


@dataclass(frozen=True, slots=True)
class BundleCandidate:
    candidate_id: str
    anchor_coord: Coord
    pattern: BundlePattern
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: str
    transport_kind: TransportKind
    throughput_factor: int
    route_probe_cost: int
    reachable: bool
    catalog_placement_ref: CatalogPlacementRef | None = None
    route_probe_start: Coord | None = None


@dataclass(frozen=True, slots=True)
class RejectedBundleCandidate:
    candidate_id: str
    anchor_coord: Coord
    pattern_id: str
    rejection_reason: CandidateRejectReason
    route_probe_cost: int | None


@dataclass(frozen=True, slots=True)
class CandidateGenerationResult:
    normal_candidates: tuple[BundleCandidate, ...]
    rejected_candidates: tuple[RejectedBundleCandidate, ...]


__all__ = [
    "BundleCandidate",
    "CandidateGenerationResult",
    "CandidateRejectReason",
    "ExtractorPlacementPolicy",
    "FixedOutputTransportPolicy",
    "RejectedBundleCandidate",
    "RouteProbeStartPolicy",
]
