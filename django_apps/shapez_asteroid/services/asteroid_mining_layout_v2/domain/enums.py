"""
Enumerations aligned with ``03_data_schema_dto.md`` and session docs (CANON).

Values are stable API strings for traces and tests.
"""

from __future__ import annotations

from enum import StrEnum


class TransportKind(StrEnum):
    """Belt vs pipe must never merge (§3.6); distinct ``TransportKind`` values only."""

    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


class PlacementCommitState(StrEnum):
    """Placement FSM states (§9.6)."""

    PROVISIONAL_PLACED = "provisional_placed"
    ROUTED_CONFIRMED = "routed_confirmed"
    QUARANTINED_UNROUTED = "quarantined_unrouted"
    ROLLED_BACK = "rolled_back"


class RouteZone(StrEnum):
    """Pass3 / reclaim cost zones (``03_data_schema_dto`` §11.1)."""

    OUTSIDE = "outside"
    BOUNDARY_VOID = "boundary_void"
    INTERNAL_VOID = "internal_void"
    FILLABLE_INTERIOR = "fillable_interior"
    PLACEMENT_CANDIDATE = "placement_candidate"
    PLACEMENT_OCCUPIED = "placement_occupied"
    BLOCKED = "blocked"


class SolverTerminationTier(StrEnum):
    """High-level run outcome (§4.4 / §19.1 ``termination``)."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    SOLVER_FAILURE = "solver_failure"


class RecoveryTrigger(StrEnum):
    """Recovery branch entry (§14 / §16.3); not a ``CommitReason``."""

    STEP4_ROUTING_FAILURE = "step4_routing_failure"
    STEP4_CAPACITY_FAILURE = "step4_capacity_failure"
    PASS3_CONNECTIVITY_BREAK = "pass3_connectivity_break"
    POST_RECLAIM_PASS3_CONNECTIVITY_BREAK = "post_reclaim_pass3_connectivity_break"
    RECLAIM_INCREMENTAL_FAILURE = "reclaim_incremental_failure"
    FINAL_VALIDATION_FAILURE = "final_validation_failure"


class CommitReason(StrEnum):
    """§13.5: success commit classification only."""

    NORMAL_GAIN = "normal_gain"
    DEGRADED_CONNECTED_RECOVERY = "degraded_connected_recovery"


class RollbackReason(StrEnum):
    """Placement rollback / removal rationale (not a commit classification)."""

    ROLLBACK_UNROUTED_PLACEMENT = "rollback_unrouted_placement"
    ROLLBACK_RECLAIM_CANDIDATE = "rollback_reclaim_candidate"


class RejectedReason(StrEnum):
    """Reject or terminal solver limit; never a ``CommitReason``."""

    REJECTED_BY_GAIN_OR_LENGTH = "rejected_by_gain_or_length"
    REJECTED_BY_CONNECTIVITY = "rejected_by_connectivity"
    REJECTED_BY_OVERLAP = "rejected_by_overlap"
    REJECTED_BY_CAPACITY = "rejected_by_capacity"
    REJECTED_BY_INTERNAL_TRANSPORT_BUDGET = "rejected_by_internal_transport_budget"
    REJECTED_BY_HARD_PROTECTED_CORRIDOR = "rejected_by_hard_protected_corridor"
    REJECTED_BY_NO_REPLACEMENT_ROUTE = "rejected_by_no_replacement_route"
    SOLVER_FAILURE_ATTEMPT_LIMIT = "solver_failure_attempt_limit"


class SourceKind(StrEnum):
    """STEP 0.5 existing layout classification (§E.1)."""

    RAW_ASTEROID_FIELD = "raw_asteroid_field"
    EXISTING_FLUID_LAYOUT = "existing_fluid_layout"
    EXISTING_SHAPE_LAYOUT = "existing_shape_layout"
    MIXED_EXISTING_LAYOUT = "mixed_existing_layout"
    UNKNOWN = "unknown"


class TransportComponentStatus(StrEnum):
    """Connected transport component role (``03_data_schema_dto.md`` §E.5)."""

    MAIN_TRUNK_CANDIDATE = "main_trunk_candidate"
    ORPHAN_COMPONENT = "orphan_component"
    SINGLE_CELL_ARTIFACT = "single_cell_artifact"
    CLEANUP_CANDIDATE = "cleanup_candidate"


class EquipmentKind(StrEnum):
    """Mining equipment row kinds for STEP 0.5 attachment (§E.7)."""

    FLUID_MINER = "fluid_miner"
    SHAPE_MINER = "shape_miner"
    EXTENSION = "extension"


class ExistingLayoutIssueCode(StrEnum):
    """STEP 0.5 issue codes (§E.8); distinct from STEP 9 ``FinalValidationReport``."""

    TRANSPORT_DISCONNECTED = "TRANSPORT_DISCONNECTED"
    ORPHAN_TRANSPORT_COMPONENT = "ORPHAN_TRANSPORT_COMPONENT"
    SINGLE_CELL_TRANSPORT_ARTIFACT = "SINGLE_CELL_TRANSPORT_ARTIFACT"
    MINER_NO_ADJACENT_TRANSPORT = "MINER_NO_ADJACENT_TRANSPORT"
    MINER_ATTACHED_TO_ORPHAN_TRANSPORT = "MINER_ATTACHED_TO_ORPHAN_TRANSPORT"
    SOURCE_KIND_AMBIGUOUS = "SOURCE_KIND_AMBIGUOUS"


class ExistingLayoutIssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
