"""Enumerations for the optimization layer (Algorithm series Phase 1–9)."""

from __future__ import annotations

from enum import IntFlag, StrEnum


class Direction(StrEnum):
    """Cardinal direction on the dense Server X/Y grid."""

    N = "n"
    E = "e"
    S = "s"
    W = "w"


class TransportKind(StrEnum):
    """Transport channel kind (matches ``DecodedCellDTO.transport_kind`` strings)."""

    NONE = "none"
    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


class RouteGoalKind(StrEnum):
    """Structured routing intent (Phase 1)."""

    TRUNK_SEED = "trunk_seed"
    CORRIDOR_ENTRY = "corridor_entry"
    EXTERNAL_MARGIN = "external_margin"
    EXISTING_TRANSPORT_ATTACHMENT = "existing_transport_attachment"
    SOFT_CORRIDOR = "soft_corridor"


class RouteProbeFailureReason(StrEnum):
    """Phase 4 probe terminal failure reasons."""

    START_BLOCKED = "start_blocked"
    NO_GOAL_CELLS = "no_goal_cells"
    EXHAUSTED = "exhausted"
    BUDGET_EXCEEDED = "budget_exceeded"
    BLOCKED_BY_OCCUPIED = "blocked_by_occupied"
    INVALID_TRANSPORT_KIND = "invalid_transport_kind"
    INVALID_ROUTE_DOMAIN = "invalid_route_domain"


class CandidateRejectReason(StrEnum):
    """Phase 3 candidate rejection reasons."""

    EXTRACTOR_NOT_RIM = "extractor_not_rim"
    EXTENSION_NOT_MINEABLE = "extension_not_mineable"
    OCCUPIED_OUTSIDE_ASTEROID = "occupied_outside_asteroid"
    OUTPUT_STUB_INSIDE_OCCUPIED = "output_stub_inside_occupied"
    OUTPUT_STUB_INVALID_COORD = "output_stub_invalid_coord"
    PATTERN_OVERLAP_SELF = "pattern_overlap_self"
    ROUTE_PROBE_UNREACHABLE = "route_probe_unreachable"


class ValidationSeverity(StrEnum):
    """Phase 8 severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssueCode(StrEnum):
    """Phase 8 issue codes (extend as validation grows)."""

    CANDIDATE_POOL_MISSING = "candidate_pool_missing"
    CANDIDATE_RESERVATION_MISMATCH = "candidate_reservation_mismatch"
    EXTRACTOR_NOT_CONNECTED = "extractor_not_connected"
    ORPHAN_TRANSPORT = "orphan_transport"
    INVALID_COORD_CONTRACT = "invalid_coord_contract"
    MATERIALIZATION_FAILED = "materialization_failed"
    RESERVED_PATH_MISMATCH = "reserved_path_mismatch"


class EvolutionConvergenceReason(StrEnum):
    """Phase 6 termination mapping."""

    MAX_GENERATION = "max_generation"
    MAX_STALL_GENERATION = "max_stall_generation"
    TIME_BUDGET_MS = "time_budget_ms"
    NO_IMPROVEMENT = "no_improvement"
    CANDIDATE_POOL_EXHAUSTED = "candidate_pool_exhausted"


class MaterializationFailureReason(StrEnum):
    """Phase K route materialization terminal failure reasons."""

    TRANSPORT_KIND_OVERLAP = "transport_kind_overlap"


class CommitConflictReason(StrEnum):
    """Phase 7 conflict reasons (StrEnum, value = stable wire string)."""

    OCCUPIED_CELL_CONFLICT = "occupied_cell_conflict"
    ROUTE_CELL_CONFLICT = "route_cell_conflict"
    TRANSPORT_KIND_CONFLICT = "transport_kind_conflict"
    HARD_BLOCKED_CONFLICT = "hard_blocked_conflict"
    HARD_PROTECTED_CONFLICT = "hard_protected_conflict"
    TRUNK_DEADLOCK = "trunk_deadlock"
    ROUTE_PROBE_FAILED = "route_probe_failed"


class ReservationState(StrEnum):
    """Phase 7 reservation lifecycle."""

    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    RELEASED = "released"


class PlacementCommitState(StrEnum):
    """Phase 7 placement FSM states."""

    PROVISIONAL = "provisional"
    FEASIBLE = "feasible"
    ROUTED = "routed"
    CONFIRMED = "confirmed"
    ROLLED_BACK = "rolled_back"


class TransportMask(IntFlag):
    """Phase 4 ``RouteCellDomain.transport_mask``."""

    NONE = 0
    SHAPE_BELT = 1
    FLUID_PIPE = 2
    BOTH = SHAPE_BELT | FLUID_PIPE


class RouteClass(StrEnum):
    """Phase 4 / 7 ``RouteCellDomain.route_class`` (v0 minimal set)."""

    VOID_EXTERNAL = "void_external"
    ASTEROID = "asteroid"
    TRANSPORT = "transport"
    TRUNK = "trunk"
    CORRIDOR_PROTECTED = "corridor_protected"
    BLOCKED = "blocked"


class TopologyNodeKind(StrEnum):
    """Phase 1 topology node classification (narrow v0)."""

    ASTEROID_FIELD = "asteroid_field"
    TRANSPORT = "transport"
    UNKNOWN = "unknown"
    VOID_EXTERNAL = "void_external"


class EdgeKind(StrEnum):
    """Phase 1 topology edge classification."""

    CARDINAL = "cardinal"
