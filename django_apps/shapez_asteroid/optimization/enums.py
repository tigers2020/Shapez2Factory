"""Enumerations for optimization layer (values aligned with phase documents)."""

from __future__ import annotations

from enum import IntFlag, StrEnum


class RouteGoalKind(StrEnum):
    TRUNK_SEED = "trunk_seed"
    CORRIDOR_ENTRY = "corridor_entry"
    EXTERNAL_MARGIN = "external_margin"
    EXISTING_TRANSPORT_ATTACHMENT = "existing_transport_attachment"
    SOFT_CORRIDOR = "soft_corridor"


class TopologyNodeKind(StrEnum):
    EXTERNAL_VOID = "external_void"
    ASTEROID_FIELD = "asteroid_field"
    RIM = "rim"
    TRANSPORT = "transport"


class EdgeKind(StrEnum):
    CARDINAL = "cardinal"


class TransportKind(StrEnum):
    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


class ExtractorPlacementPolicy(StrEnum):
    """Candidate pool constraint only; not install order or commit."""

    RIM_ONLY = "rim_only"


class TransportMask(IntFlag):
    """Phase 4 bitmask; wrong transport kind is enforced via mask, not ad-hoc strings."""

    NONE = 0
    SHAPE_BELT = 1
    FLUID_PIPE = 2
    BOTH = SHAPE_BELT | FLUID_PIPE


class RouteClass(StrEnum):
    STANDARD = "standard"
    PREFERRED_TRUNK = "preferred_trunk"
    NARROW_CORRIDOR = "narrow_corridor"
    ASTEROID_CARVE = "asteroid_carve"


class RouteProbeFailureReason(StrEnum):
    START_BLOCKED = "start_blocked"
    NO_GOAL_CELLS = "no_goal_cells"
    EXHAUSTED = "exhausted"
    BUDGET_EXCEEDED = "budget_exceeded"
    BLOCKED_BY_OCCUPIED = "blocked_by_occupied"
    INVALID_TRANSPORT_KIND = "invalid_transport_kind"
    INVALID_ROUTE_DOMAIN = "invalid_route_domain"


class CandidateRejectReason(StrEnum):
    EXTRACTOR_NOT_RIM = "extractor_not_rim"
    EXTENSION_NOT_MINEABLE = "extension_not_mineable"
    OCCUPIED_OUTSIDE_ASTEROID = "occupied_outside_asteroid"
    OUTPUT_STUB_INSIDE_OCCUPIED = "output_stub_inside_occupied"
    OUTPUT_STUB_INVALID_COORD = "output_stub_invalid_coord"
    PATTERN_OVERLAP_SELF = "pattern_overlap_self"
    ROUTE_PROBE_UNREACHABLE = "route_probe_unreachable"


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssueCode(StrEnum):
    ORPHAN_TRANSPORT = "orphan_transport"
    EXTRACTOR_OUTPUT_DISCONNECTED = "extractor_output_disconnected"
    INVALID_OVERLAP = "invalid_overlap"
    INVALID_COORD_CONTRACT = "invalid_coord_contract"
    RESERVED_PATH_MISMATCH = "reserved_path_mismatch"
    CONFIRMED_RESERVATION_MISSING = "confirmed_reservation_missing"
    TRANSPORT_KIND_MISMATCH = "transport_kind_mismatch"
    EXTENSION_ATTACHMENT_INVALID = "extension_attachment_invalid"
    EXTENSION_COUNT_EXCEEDED = "extension_count_exceeded"
    ROUTE_GOAL_MISMATCH = "route_goal_mismatch"


class EvolutionConvergenceReason(StrEnum):
    MAX_GENERATION = "max_generation"
    MAX_STALL_GENERATION = "max_stall_generation"
    TIME_BUDGET_MS = "time_budget_ms"
    NO_IMPROVEMENT = "no_improvement"
    CANDIDATE_POOL_EXHAUSTED = "candidate_pool_exhausted"


class CommitConflictReason(StrEnum):
    OCCUPIED_CELL_CONFLICT = "occupied_cell_conflict"
    ROUTE_CELL_CONFLICT = "route_cell_conflict"
    TRANSPORT_KIND_CONFLICT = "transport_kind_conflict"
    HARD_PROTECTED_CONFLICT = "hard_protected_conflict"
    TRUNK_DEADLOCK = "trunk_deadlock"
    ROUTE_PROBE_FAILED = "route_probe_failed"


class OptimizationReplayEventType(StrEnum):
    OPTIMIZATION_INPUT_LOADED = "optimization.input_loaded"
    PATTERN_GENERATED = "pattern.generated"
    CANDIDATE_GENERATED = "candidate.generated"
    CANDIDATE_REJECTED = "candidate.rejected"
    ROUTE_PROBE_SUCCEEDED = "route_probe.succeeded"
    ROUTE_PROBE_FAILED = "route_probe.failed"
    GENOME_GENERATED = "genome.generated"
    GENOME_EVALUATED = "genome.evaluated"
    GENERATION_COMPLETED = "generation.completed"
    BEST_GENOME_SELECTED = "best_genome.selected"
    ROUTE_COMMIT_ATTEMPTED = "route.commit_attempted"
    ROUTE_COMMITTED = "route.committed"
    ROUTE_ROLLED_BACK = "route.rolled_back"
    VALIDATION_COMPLETED = "validation.completed"


class ReservationState(StrEnum):
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    RELEASED = "released"


class PlacementCommitState(StrEnum):
    PROVISIONAL = "provisional"
    FEASIBLE = "feasible"
    ROUTED = "routed"
    CONFIRMED = "confirmed"
    ROLLED_BACK = "rolled_back"


class CardinalDirection(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
