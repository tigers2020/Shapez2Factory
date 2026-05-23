"""Macro compile/probe rejection reasons (RTTP v1 MacroBundleT3, PR-A)."""

from __future__ import annotations

from enum import StrEnum


class MacroRejectReason(StrEnum):
    CHILD_OCCUPANCY_OVERLAP = "child_occupancy_overlap"
    RING_PORT_MISMATCH = "ring_port_mismatch"
    SHARED_LIFT_UNREACHABLE = "shared_lift_unreachable"
    CHILD_NOT_IN_NORMAL_POOL = "child_not_in_normal_pool"
    TRANSPORT_KIND_MISMATCH = "transport_kind_mismatch"
    PROTECTED_CORRIDOR_CONFLICT = "protected_corridor_conflict"
    EXCEEDS_MAX_MACRO_CANDIDATES = "exceeds_max_macro_candidates"


__all__ = ["MacroRejectReason"]
