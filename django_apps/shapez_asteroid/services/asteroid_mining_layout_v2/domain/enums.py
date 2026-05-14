"""
Enumerations aligned with ``03_data_schema_dto.md`` (CANON).

Values are stable API strings for traces and tests.
"""

from __future__ import annotations

from enum import Enum


class TransportKind(str, Enum):
    """Belt vs pipe must never merge (§3.6)."""

    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


class PlacementCommitState(str, Enum):
    """Placement FSM states (§9.6). MVP resolves quarantine before final validation."""

    PROVISIONAL_PLACED = "provisional_placed"
    ROUTED_CONFIRMED = "routed_confirmed"
    QUARANTINED_UNROUTED = "quarantined_unrouted"
    ROLLED_BACK = "rolled_back"


class SourceKind(str, Enum):
    """STEP 0.5 existing layout classification (§E.1)."""

    RAW_ASTEROID_FIELD = "raw_asteroid_field"
    EXISTING_FLUID_LAYOUT = "existing_fluid_layout"
    EXISTING_SHAPE_LAYOUT = "existing_shape_layout"
    MIXED_EXISTING_LAYOUT = "mixed_existing_layout"
    UNKNOWN = "unknown"


class SolverTermination(str, Enum):
    """High-level run outcome (§4.4)."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    SOLVER_FAILURE = "solver_failure"
