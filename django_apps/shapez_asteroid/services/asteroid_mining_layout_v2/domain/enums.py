"""
Enumerations aligned with ``03_data_schema_dto.md`` and session docs (CANON).

Values are stable API strings for traces and tests.
"""

from __future__ import annotations

from enum import Enum


class TransportKind(str, Enum):
    """Belt vs pipe must never merge (§3.6); distinct ``TransportKind`` values only."""

    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


class PlacementCommitState(str, Enum):
    """Placement FSM states (§9.6)."""

    PROVISIONAL_PLACED = "provisional_placed"
    ROUTED_CONFIRMED = "routed_confirmed"
    QUARANTINED_UNROUTED = "quarantined_unrouted"
    ROLLED_BACK = "rolled_back"


class RouteZone(str, Enum):
    """Pass3 / reclaim cost zones (``03_data_schema_dto`` §11.1)."""

    OUTSIDE = "outside"
    BOUNDARY_VOID = "boundary_void"
    INTERNAL_VOID = "internal_void"
    FILLABLE_INTERIOR = "fillable_interior"
    PLACEMENT_CANDIDATE = "placement_candidate"
    PLACEMENT_OCCUPIED = "placement_occupied"
    BLOCKED = "blocked"


class SolverTerminationTier(str, Enum):
    """High-level run outcome (§4.4 / §19.1 ``termination``)."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    SOLVER_FAILURE = "solver_failure"


class RecoveryTrigger(str, Enum):
    """Recovery branch entry (§14 / §16.3); not a ``CommitReason``."""

    STEP4_ROUTING_FAILURE = "step4_routing_failure"
    STEP4_CAPACITY_FAILURE = "step4_capacity_failure"
    PASS3_CONNECTIVITY_BREAK = "pass3_connectivity_break"
    POST_RECLAIM_PASS3_CONNECTIVITY_BREAK = "post_reclaim_pass3_connectivity_break"
    RECLAIM_INCREMENTAL_FAILURE = "reclaim_incremental_failure"
    FINAL_VALIDATION_FAILURE = "final_validation_failure"


class CommitReason(str, Enum):
    """§13.5: success commit classification only."""

    NORMAL_GAIN = "normal_gain"
    DEGRADED_CONNECTED_RECOVERY = "degraded_connected_recovery"


class RollbackReason(str, Enum):
    """Placement rollback / removal rationale (not a commit classification)."""

    ROLLBACK_UNROUTED_PLACEMENT = "rollback_unrouted_placement"
    ROLLBACK_RECLAIM_CANDIDATE = "rollback_reclaim_candidate"


class RejectedReason(str, Enum):
    """Reject or terminal solver limit; never a ``CommitReason``."""

    REJECTED_BY_GAIN_OR_LENGTH = "rejected_by_gain_or_length"
    REJECTED_BY_CONNECTIVITY = "rejected_by_connectivity"
    REJECTED_BY_OVERLAP = "rejected_by_overlap"
    REJECTED_BY_CAPACITY = "rejected_by_capacity"
    REJECTED_BY_INTERNAL_TRANSPORT_BUDGET = "rejected_by_internal_transport_budget"
    REJECTED_BY_HARD_PROTECTED_CORRIDOR = "rejected_by_hard_protected_corridor"
    REJECTED_BY_NO_REPLACEMENT_ROUTE = "rejected_by_no_replacement_route"
    SOLVER_FAILURE_ATTEMPT_LIMIT = "solver_failure_attempt_limit"


class SourceKind(str, Enum):
    """STEP 0.5 existing layout classification (§E.1)."""

    RAW_ASTEROID_FIELD = "raw_asteroid_field"
    EXISTING_FLUID_LAYOUT = "existing_fluid_layout"
    EXISTING_SHAPE_LAYOUT = "existing_shape_layout"
    MIXED_EXISTING_LAYOUT = "mixed_existing_layout"
    UNKNOWN = "unknown"
