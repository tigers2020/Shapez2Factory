"""RTTP v1 MacroBundleT3 DTOs, compiler, and probe (PR-A + PR-B)."""

from django_apps.asteroid_lab.optimization.macros.macro_compiler import (
    MacroCompileConfig,
    MacroGenerationResult,
    RejectedMacroBundle,
    compile_macros,
)
from django_apps.asteroid_lab.optimization.macros.macro_dtos import (
    MacroBundleCandidate,
    MacroBundleT3,
    SharedLiftStubPlan,
    SharedRingPortIntent,
    canonical_shared_lift_stub_plan_json,
    canonical_shared_ring_port_intent_json,
    child_occupancy_overlaps,
    derive_macro_id,
    union_child_occupied_cells,
)
from django_apps.asteroid_lab.optimization.macros.macro_probe import (
    MacroProbeResult,
    probe_macro_shared_lift,
)
from django_apps.asteroid_lab.optimization.macros.macro_reject_reason import MacroRejectReason

__all__ = [
    "MacroBundleCandidate",
    "MacroBundleT3",
    "MacroCompileConfig",
    "MacroGenerationResult",
    "MacroProbeResult",
    "MacroRejectReason",
    "RejectedMacroBundle",
    "SharedLiftStubPlan",
    "SharedRingPortIntent",
    "canonical_shared_lift_stub_plan_json",
    "canonical_shared_ring_port_intent_json",
    "child_occupancy_overlaps",
    "compile_macros",
    "derive_macro_id",
    "probe_macro_shared_lift",
    "union_child_occupied_cells",
]
