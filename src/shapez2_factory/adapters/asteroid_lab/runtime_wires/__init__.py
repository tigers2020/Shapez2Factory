"""Solver runtime wire serde (replay projection only)."""

from shapez2_factory.adapters.asteroid_lab.runtime_wires.deserialize import (
    RuntimeWiresProjectionBundle,
    deserialize_l3_wire,
    deserialize_l4_wire,
    deserialize_l5_wire,
    deserialize_runtime_wires_document,
)
from shapez2_factory.adapters.asteroid_lab.runtime_wires.envelope import (
    COMPLETE_MAP_MANIFEST_PATH_KEY,
    DIAGNOSTIC_L3_ORDER_INVALID,
    DIAGNOSTIC_L4_PLACEMENT_MISMATCH,
    DIAGNOSTIC_SCHEMA_UNKNOWN,
    L3_WIRE_VERSION,
    L4_WIRE_VERSION,
    MANIFEST_PATH_KEY,
    RUNTIME_WIRE_KIND,
    RUNTIME_WIRES_ARTIFACT_REL_PATH,
    RUNTIME_WIRES_SCHEMA_VERSION,
    LayerOutcome,
    RuntimeWireValidationError,
)
from shapez2_factory.adapters.asteroid_lab.runtime_wires.serialize import (
    build_runtime_wires_document,
    serialize_layer02_wire,
    serialize_layer03_wire,
    serialize_layer04_wire,
    serialize_layer05_wire,
)

__all__ = [
    "COMPLETE_MAP_MANIFEST_PATH_KEY",
    "DIAGNOSTIC_L3_ORDER_INVALID",
    "DIAGNOSTIC_L4_PLACEMENT_MISMATCH",
    "DIAGNOSTIC_SCHEMA_UNKNOWN",
    "L3_WIRE_VERSION",
    "L4_WIRE_VERSION",
    "MANIFEST_PATH_KEY",
    "RUNTIME_WIRES_ARTIFACT_REL_PATH",
    "RUNTIME_WIRES_SCHEMA_VERSION",
    "RUNTIME_WIRE_KIND",
    "LayerOutcome",
    "RuntimeWireValidationError",
    "RuntimeWiresProjectionBundle",
    "build_runtime_wires_document",
    "deserialize_l3_wire",
    "deserialize_l4_wire",
    "deserialize_l5_wire",
    "deserialize_runtime_wires_document",
    "serialize_layer02_wire",
    "serialize_layer03_wire",
    "serialize_layer04_wire",
    "serialize_layer05_wire",
]
