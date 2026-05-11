"""Final validation DTO contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinalValidationReport:
    """STEP9 final validation 결과 DTO.

    Capacity / trunk rated limits are not represented here; they stay trace-only in STEP4
    ``trunk_load`` (see ``validate_final_mining_layout`` module docstring).
    """

    geometry_valid: bool
    connectivity_valid: bool
    disconnected_stub_count: int
    quarantined_unrouted_count: int
    provisional_placed_row_count: int
    orphan_transport_count: int
    overlap_violation_count: int
    missing_stub_count: int
    missing_extractor_rotation_count: int
    extractor_count: int = 0
    extension_count: int = 0
    transport_cell_count: int = 0
    transport_connectivity_ok: bool = True
