"""Layer 03 rim bundle candidate DTOs and normal-pool invariant factory."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
        Layer03Observability,
    )

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_MINING_BUNDLES
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind, TransportKind
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

Layer03Slug = Literal["layer_03_rim_mining_bundles"]


class RouteProbeStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED_BUDGET = "skipped_budget"
    SKIPPED_GEOMETRY = "skipped_geometry"
    SKIPPED_NO_GOAL = "skipped_no_goal"


class CandidateRejectReason(StrEnum):
    NO_EXTERIOR_VOID_NEIGHBOR = "no_exterior_void_neighbor"
    NO_ROUTE_GOAL_FOR_TRANSPORT_KIND = "no_route_goal_for_transport_kind"
    LOCAL_GEOMETRY_INVALID = "local_geometry_invalid"
    MINING_CELL_OFF_FIELD = "mining_cell_off_field"
    TRANSPORT_STUB_NOT_IN_VOID = "transport_stub_not_in_void"
    TRANSPORT_COLLIDES_WITH_FIELD = "transport_collides_with_field"
    TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT = "transport_collides_with_mining_equipment"
    EXTERIOR_ENTRY_NOT_REACHABLE = "exterior_entry_not_reachable"
    EXTERIOR_CONNECTOR_UNREACHABLE = "exterior_connector_unreachable"
    ROUTE_PROBE_FAILED = "route_probe_failed"
    BUDGET_EXHAUSTED = "budget_exhausted"


class Layer03SkipReason(StrEnum):
    NONE = "none"
    MISSING_EXTERIOR_CONNECTION_PLAN = "missing_exterior_connection_plan"
    NO_ROUTE_GOALS = "no_route_goals"
    EMPTY_MINER_SEED_CATALOG = "empty_miner_seed_catalog"
    BUDGET_EXHAUSTED = "budget_exhausted"


class BundleCellRole(StrEnum):
    MINER = "miner"
    EXTENSION = "extension"
    TRANSPORT_STUB = "transport_stub"


@dataclass(frozen=True, slots=True)
class BundlePlacement:
    coord: Coord
    layout_t: str
    rotation: int
    cell_role: BundleCellRole


@dataclass(frozen=True, slots=True)
class BundleCandidate:
    candidate_id: str
    layer_slug: Layer03Slug
    gene_key: str
    pattern_id: str
    intrinsic_priority_rank: int
    anchor_coord: Coord
    output_dir: Direction
    rotation: int
    resource_kind: ResourceKind
    transport_kind: TransportKind
    equivalence_key: str
    mining_occupied_cells: frozenset[Coord]
    transport_stub_cells: frozenset[Coord]
    route_probe_start_coord: Coord
    placements: tuple[BundlePlacement, ...]
    throughput_factor: int
    topology_signature: str

    def __post_init__(self) -> None:
        if self.layer_slug != LAYER_03_RIM_MINING_BUNDLES:
            msg = f"layer_slug must be {LAYER_03_RIM_MINING_BUNDLES!r}"
            raise ValueError(msg)
        if self.route_probe_start_coord in self.mining_occupied_cells:
            msg = "route_probe_start_coord must not be in mining_occupied_cells"
            raise ValueError(msg)
        if self.mining_occupied_cells & self.transport_stub_cells:
            msg = "mining_occupied_cells must not overlap transport_stub_cells"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class RouteProbeResult:
    reached_goal: bool
    goal_coord: Coord | None
    path_coords: tuple[Coord, ...]
    steps_expanded: int
    transport_kind: TransportKind
    route_cost: int = 0
    field_route_cell_count: int = 0

    def proposed_transport_cells(self, *, stub_cells: frozenset[Coord]) -> frozenset[Coord]:
        """Return the candidate's proposed transport cells only.

        This is not the full ExteriorTransportDomain.placeable_cells component.
        It is limited to seed-projected stubs plus the explicit probe path.
        """
        return stub_cells | frozenset(self.path_coords)


@dataclass(frozen=True, slots=True)
class RouteProbedBundleCandidate:
    candidate: BundleCandidate
    route_probe_status: RouteProbeStatus
    route_probe_result: RouteProbeResult | None
    route_goal_id: str | None
    reject_reason: CandidateRejectReason | None

    def __post_init__(self) -> None:
        _validate_route_probed_bundle_candidate(self)


@dataclass(frozen=True, slots=True)
class Layer03ExpansionMetrics:
    rim_anchor_count: int
    seed_projection_attempt_count: int
    local_geometry_rejected_count: int
    route_probe_attempt_count: int
    route_probe_succeeded_count: int
    route_probe_failed_count: int
    dedupe_duplicate_count: int
    normal_candidate_count: int
    diagnostic_rejected_count: int
    budget_skipped_count: int
    layer_skip_reason: Layer03SkipReason
    reject_reason_counts: tuple[tuple[str, int], ...] = ()
    exterior_direction_candidate_count: int = 0
    direction_seed_attempt_count: int = 0
    mining_footprint_prefilter_rejected_count: int = 0
    field_route_cell_count_total: int = 0
    weighted_route_cost_total: int = 0
    transport_blocked_by_mining_count: int = 0

    @classmethod
    def empty(cls) -> Layer03ExpansionMetrics:
        return cls(
            rim_anchor_count=0,
            seed_projection_attempt_count=0,
            local_geometry_rejected_count=0,
            route_probe_attempt_count=0,
            route_probe_succeeded_count=0,
            route_probe_failed_count=0,
            dedupe_duplicate_count=0,
            normal_candidate_count=0,
            diagnostic_rejected_count=0,
            budget_skipped_count=0,
            layer_skip_reason=Layer03SkipReason.NONE,
            reject_reason_counts=(),
            exterior_direction_candidate_count=0,
            direction_seed_attempt_count=0,
            mining_footprint_prefilter_rejected_count=0,
            field_route_cell_count_total=0,
            weighted_route_cost_total=0,
            transport_blocked_by_mining_count=0,
        )


@dataclass(frozen=True, slots=True)
class RimBundleCandidateSet:
    normal_candidates: tuple[RouteProbedBundleCandidate, ...]
    diagnostic_rejected_candidates: tuple[RouteProbedBundleCandidate, ...]
    metrics: Layer03ExpansionMetrics
    observability: Layer03Observability


def _validate_route_probed_bundle_candidate(entry: RouteProbedBundleCandidate) -> None:
    status = entry.route_probe_status
    if status == RouteProbeStatus.SUCCEEDED:
        if entry.route_probe_result is None:
            msg = "route_probe_result is required when route_probe_status is SUCCEEDED"
            raise ValueError(msg)
        if entry.route_goal_id is None:
            msg = "route_goal_id is required when route_probe_status is SUCCEEDED"
            raise ValueError(msg)
        if not entry.route_probe_result.reached_goal:
            msg = (
                "route_probe_result.reached_goal must be true "
                "when route_probe_status is SUCCEEDED"
            )
            raise ValueError(msg)
        _validate_succeeded_path_endpoints(entry.candidate, entry.route_probe_result)
        return
    if entry.route_probe_result is not None:
        msg = "route_probe_result must be None unless route_probe_status is SUCCEEDED"
        raise ValueError(msg)
    if entry.route_goal_id is not None:
        msg = "route_goal_id must be None unless route_probe_status is SUCCEEDED"
        raise ValueError(msg)


def _validate_succeeded_path_endpoints(
    candidate: BundleCandidate,
    result: RouteProbeResult,
) -> None:
    if not result.path_coords:
        msg = "path_coords must be non-empty when route_probe_status is SUCCEEDED"
        raise ValueError(msg)
    if result.path_coords[0] != candidate.route_probe_start_coord:
        msg = "path_coords[0] must equal candidate.route_probe_start_coord"
        raise ValueError(msg)
    if result.goal_coord is None:
        msg = "goal_coord is required when route_probe_status is SUCCEEDED"
        raise ValueError(msg)
    if result.path_coords[-1] != result.goal_coord:
        msg = "path_coords[-1] must equal route_probe_result.goal_coord"
        raise ValueError(msg)


def build_rim_bundle_candidate_set(
    *,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    diagnostic_rejected_candidates: tuple[RouteProbedBundleCandidate, ...],
    metrics: Layer03ExpansionMetrics,
    observability: Layer03Observability,
) -> RimBundleCandidateSet:
    for entry in normal_candidates:
        if entry.route_probe_status != RouteProbeStatus.SUCCEEDED:
            msg = (
                "normal_candidates must contain only route_probe_status SUCCEEDED; "
                f"got {entry.route_probe_status!r}"
            )
            raise ValueError(msg)
    for entry in diagnostic_rejected_candidates:
        if entry.route_probe_status == RouteProbeStatus.SUCCEEDED:
            msg = "diagnostic_rejected_candidates must not contain SUCCEEDED entries"
            raise ValueError(msg)
    if metrics.normal_candidate_count != len(normal_candidates):
        msg = "metrics.normal_candidate_count must equal len(normal_candidates)"
        raise ValueError(msg)
    if metrics.diagnostic_rejected_count != len(diagnostic_rejected_candidates):
        msg = "metrics.diagnostic_rejected_count must equal len(diagnostic_rejected_candidates)"
        raise ValueError(msg)
    if observability.skip_reason is not metrics.layer_skip_reason:
        msg = "observability.skip_reason must match metrics.layer_skip_reason"
        raise ValueError(msg)
    if observability.normal_candidate_count != metrics.normal_candidate_count:
        msg = "observability.normal_candidate_count must match metrics.normal_candidate_count"
        raise ValueError(msg)
    if observability.rim_anchor_count != metrics.rim_anchor_count:
        msg = "observability.rim_anchor_count must match metrics.rim_anchor_count"
        raise ValueError(msg)
    return RimBundleCandidateSet(
        normal_candidates=normal_candidates,
        diagnostic_rejected_candidates=diagnostic_rejected_candidates,
        metrics=metrics,
        observability=observability,
    )


def make_bundle_candidate_for_test(
    *,
    gene_key: str = "miner_seed_m3e_01",
    pattern_id: str = "m3e_01",
    intrinsic_priority_rank: int = 1,
    anchor_coord: Coord = (3, 4),
    output_dir: Direction = Direction.E,
    rotation: int = 0,
    resource_kind: ResourceKind = ResourceKind.SHAPE,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
    equivalence_key: str = "equiv_test_key",
    mining_occupied_cells: frozenset[Coord] | None = None,
    transport_stub_cells: frozenset[Coord] | None = None,
    route_probe_start_coord: Coord = (5, 4),
    throughput_factor: int = 16,
    topology_signature: str = "topo_test",
) -> BundleCandidate:
    mining = (
        frozenset({anchor_coord, (4, 4)})
        if mining_occupied_cells is None
        else mining_occupied_cells
    )
    transport = (
        frozenset({route_probe_start_coord})
        if transport_stub_cells is None
        else transport_stub_cells
    )
    candidate_id = (
        f"layer_03:{gene_key}:{anchor_coord[0]}:{anchor_coord[1]}:"
        f"{output_dir.value}:{rotation}:{transport_kind.value}"
    )
    placements = (
        BundlePlacement(
            coord=anchor_coord,
            layout_t="Layout_ShapeMiner",
            rotation=rotation,
            cell_role=BundleCellRole.MINER,
        ),
        BundlePlacement(
            coord=route_probe_start_coord,
            layout_t="SpaceBelt_Forward",
            rotation=rotation,
            cell_role=BundleCellRole.TRANSPORT_STUB,
        ),
    )
    return BundleCandidate(
        candidate_id=candidate_id,
        layer_slug=cast(Layer03Slug, LAYER_03_RIM_MINING_BUNDLES),
        gene_key=gene_key,
        pattern_id=pattern_id,
        intrinsic_priority_rank=intrinsic_priority_rank,
        anchor_coord=anchor_coord,
        output_dir=output_dir,
        rotation=rotation,
        resource_kind=resource_kind,
        transport_kind=transport_kind,
        equivalence_key=equivalence_key,
        mining_occupied_cells=mining,
        transport_stub_cells=transport,
        route_probe_start_coord=route_probe_start_coord,
        placements=placements,
        throughput_factor=throughput_factor,
        topology_signature=topology_signature,
    )


__all__ = [
    "BundleCandidate",
    "BundleCellRole",
    "BundlePlacement",
    "CandidateRejectReason",
    "Layer03ExpansionMetrics",
    "Layer03SkipReason",
    "Layer03Slug",
    "RimBundleCandidateSet",
    "RouteProbeResult",
    "RouteProbeStatus",
    "RouteProbedBundleCandidate",
    "build_rim_bundle_candidate_set",
    "make_bundle_candidate_for_test",
]
