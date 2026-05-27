"""ELCP exterior lane plan, assignment, and ELCP-TM trunk/evidence DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal, TransportKind

ACTIVATION_REASON_CAPACITY_EXHAUSTED = "capacity_exhausted"


@dataclass(frozen=True, slots=True)
class ExteriorTransportLane:
    """Immutable static lane contract (plan layer)."""

    lane_id: str
    transport_kind: TransportKind
    connector_goal: RouteGoal
    capacity_per_min: Decimal
    target_load_per_min: Decimal
    anchor_coord: Coord


@dataclass(frozen=True, slots=True)
class ExteriorLaneAssignmentState:
    """Commit-time assigned throughput accumulator (separate from plan DTOs)."""

    lane_id: str
    assigned_load_per_min: Decimal


@dataclass(frozen=True, slots=True)
class ExteriorLaneCapacityPlan:
    """Static exterior lane capacity plan for one transport kind."""

    transport_kind: TransportKind
    max_asteroid_throughput_per_min: Decimal
    lane_capacity_per_min: Decimal
    required_lane_count: int
    lanes: tuple[ExteriorTransportLane, ...]


@dataclass(frozen=True, slots=True)
class ExteriorLaneTrunkState:
    """Per-lane shared trunk geometry and activation (commit-time, ELCP-TM)."""

    lane_id: str
    transport_kind: TransportKind
    active: bool
    assigned_load_per_min: Decimal
    trunk_cells: frozenset[Coord]
    connector_coord: Coord


@dataclass(frozen=True, slots=True)
class ExteriorLaneRouteEvidence:
    """Per-candidate branch/trunk reservation evidence (output-only)."""

    candidate_id: str
    lane_id: str
    candidate_throughput_per_min: Decimal
    branch_cells: tuple[Coord, ...]
    reused_trunk_cells: tuple[Coord, ...]
    new_trunk_cells: tuple[Coord, ...]
    reached_connector_coord: Coord | None
    reached_trunk_coord: Coord | None


@dataclass(frozen=True, slots=True)
class ExteriorLaneActivationEvidence:
    """Lane open event when fill-first activates the next lane index."""

    activated_lane_id: str
    previous_lane_id: str
    previous_lane_assigned_load_per_min: Decimal
    previous_lane_capacity_per_min: Decimal
    trigger_candidate_id: str
    trigger_candidate_throughput_per_min: Decimal
    activation_reason: str


@dataclass(frozen=True, slots=True)
class ExteriorLaneCommitValidationSnapshot:
    """ELCP commit evidence for read-only validation (contracts-only boundary)."""

    exterior_lane_assignments: tuple[dict[str, object], ...] = ()
    exterior_lane_assignment_state: tuple[ExteriorLaneAssignmentState, ...] = ()
    exterior_lane_activations: tuple[ExteriorLaneActivationEvidence, ...] = ()
    exterior_lane_trunk_states: tuple[ExteriorLaneTrunkState, ...] = ()
    exterior_lane_route_evidence: tuple[ExteriorLaneRouteEvidence, ...] = ()


__all__ = [
    "ACTIVATION_REASON_CAPACITY_EXHAUSTED",
    "ExteriorLaneActivationEvidence",
    "ExteriorLaneAssignmentState",
    "ExteriorLaneCommitValidationSnapshot",
    "ExteriorLaneCapacityPlan",
    "ExteriorLaneRouteEvidence",
    "ExteriorLaneTrunkState",
    "ExteriorTransportLane",
]
