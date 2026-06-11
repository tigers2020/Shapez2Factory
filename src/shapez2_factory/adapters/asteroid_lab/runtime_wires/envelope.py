"""Runtime wire envelope constants and validation errors."""

from __future__ import annotations

from enum import StrEnum

RUNTIME_WIRES_SCHEMA_VERSION = "solver_runtime_wires_v1"
RUNTIME_WIRES_ARTIFACT_REL_PATH = "output/solver_runtime_wires.v1.json"
MANIFEST_PATH_KEY = "solver_runtime_wires"
COMPLETE_MAP_MANIFEST_PATH_KEY = "layer01_complete_map"

RUNTIME_WIRE_KIND = "solver_runtime_projection"

L3_WIRE_VERSION = "integrated_rim_greedy_result_v1"
L4_WIRE_VERSION = "layer04_inner_fill_result_v1"

DIAGNOSTIC_L3_ORDER_INVALID = "runtime_wire_l3_order_invalid"
DIAGNOSTIC_L4_PLACEMENT_MISMATCH = "runtime_wire_l4_placement_mismatch"
DIAGNOSTIC_SCHEMA_UNKNOWN = "runtime_wire_schema_unknown"


class LayerOutcome(StrEnum):
    COMPLETED = "completed"
    PARTIAL_BUDGET = "partial_budget"
    SKIPPED = "skipped"
    FAILED = "failed"


class RuntimeWireValidationError(ValueError):
    code: str

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


__all__ = [
    "COMPLETE_MAP_MANIFEST_PATH_KEY",
    "DIAGNOSTIC_L3_ORDER_INVALID",
    "DIAGNOSTIC_L4_PLACEMENT_MISMATCH",
    "DIAGNOSTIC_SCHEMA_UNKNOWN",
    "L3_WIRE_VERSION",
    "L4_WIRE_VERSION",
    "LayerOutcome",
    "MANIFEST_PATH_KEY",
    "RUNTIME_WIRES_ARTIFACT_REL_PATH",
    "RUNTIME_WIRES_SCHEMA_VERSION",
    "RUNTIME_WIRE_KIND",
    "RuntimeWireValidationError",
]
