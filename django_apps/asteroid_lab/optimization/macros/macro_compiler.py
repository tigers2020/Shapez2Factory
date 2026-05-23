"""Compile MacroBundleT3 candidates from normal child pool (RTTP v1, PR-B)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.macros.macro_dtos import (
    MacroBundleCandidate,
    MacroBundleT3,
    SharedLiftStubPlan,
    SharedRingPortIntent,
    child_occupancy_overlaps,
    derive_macro_id,
    union_child_occupied_cells,
)
from django_apps.asteroid_lab.optimization.macros.macro_probe import probe_macro_shared_lift
from django_apps.asteroid_lab.optimization.macros.macro_reject_reason import MacroRejectReason
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


@dataclass(frozen=True, slots=True)
class MacroCompileConfig:
    max_macro_candidates: int = 64
    max_probe_expansions: int = 500


@dataclass(frozen=True, slots=True)
class RejectedMacroBundle:
    child_a_id: str
    child_b_id: str
    child_c_id: str
    rejection_reason: MacroRejectReason
    route_probe_cost: int | None = None


@dataclass(frozen=True, slots=True)
class MacroGenerationResult:
    macro_normal: tuple[MacroBundleCandidate, ...]
    macro_rejected: tuple[RejectedMacroBundle, ...]


def _derive_shared_lift_stub_plan(skeleton: RttpSkeleton) -> SharedLiftStubPlan | None:
    if not skeleton.lift_columns:
        return None
    column = skeleton.lift_columns[0]
    lift_coords = frozenset({column.platform_coord, column.lift_coord})
    return SharedLiftStubPlan(
        lift_column_coords=lift_coords,
        trunk_entry_coord=column.lift_coord,
        reserved_route_cells=lift_coords,
    )


def _derive_shared_ring_port_intent(skeleton: RttpSkeleton) -> SharedRingPortIntent | None:
    if not skeleton.ring_ports:
        return None
    port = skeleton.ring_ports[0]
    return SharedRingPortIntent(
        primary_ring_port_coord=port.coord,
        preferred_dir=port.preferred_dir,
        secondary_port_coords=frozenset(),
    )


def _sorted_child_ids(children: tuple[BundleCandidate, ...]) -> tuple[str, str, str]:
    ids = sorted(child.candidate_id for child in children)
    return ids[0], ids[1], ids[2]


def _reject(
    children: tuple[BundleCandidate, ...],
    reason: MacroRejectReason,
    *,
    route_probe_cost: int | None = None,
) -> RejectedMacroBundle:
    child_a_id, child_b_id, child_c_id = _sorted_child_ids(children)
    return RejectedMacroBundle(
        child_a_id=child_a_id,
        child_b_id=child_b_id,
        child_c_id=child_c_id,
        rejection_reason=reason,
        route_probe_cost=route_probe_cost,
    )


def _build_macro_bundle(
    children: tuple[BundleCandidate, ...],
    shared_lift: SharedLiftStubPlan,
    shared_ring: SharedRingPortIntent,
) -> MacroBundleT3:
    sorted_children = tuple(sorted(children, key=lambda c: c.candidate_id))
    child_a_id, child_b_id, child_c_id = _sorted_child_ids(sorted_children)
    combined = union_child_occupied_cells(sorted_children)
    macro_id = derive_macro_id(
        child_a_id=child_a_id,
        child_b_id=child_b_id,
        child_c_id=child_c_id,
        shared_lift_stub_plan=shared_lift,
        shared_ring_port_intent=shared_ring,
    )
    return MacroBundleT3(
        macro_id=macro_id,
        child_a_id=child_a_id,
        child_b_id=child_b_id,
        child_c_id=child_c_id,
        children=sorted_children,
        shared_lift_stub_plan=shared_lift,
        shared_ring_port_intent=shared_ring,
        combined_occupied_cells=combined,
        macro_throughput_factor=sum(c.throughput_factor for c in sorted_children),
        topology_signature=tuple(c.pattern.pattern_id for c in sorted_children),
    )


def compile_macros(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    config: MacroCompileConfig | None = None,
) -> MacroGenerationResult:
    """Enumerate child triples; admit macros that pass geometry and shared-lift probe."""

    compile_config = config or MacroCompileConfig()
    domain = build_route_domain_from_skeleton(skeleton, inp)
    sorted_pool = tuple(sorted(normal_candidates, key=lambda c: c.candidate_id))

    shared_lift = _derive_shared_lift_stub_plan(skeleton)
    shared_ring = _derive_shared_ring_port_intent(skeleton)

    macro_normal: list[MacroBundleCandidate] = []
    macro_rejected: list[RejectedMacroBundle] = []

    for triple in combinations(sorted_pool, 3):
        children = triple
        if len(macro_normal) >= compile_config.max_macro_candidates:
            macro_rejected.append(
                _reject(children, MacroRejectReason.EXCEEDS_MAX_MACRO_CANDIDATES)
            )
            continue

        if child_occupancy_overlaps(children):
            macro_rejected.append(_reject(children, MacroRejectReason.CHILD_OCCUPANCY_OVERLAP))
            continue

        if shared_lift is None or shared_ring is None:
            macro_rejected.append(_reject(children, MacroRejectReason.SHARED_LIFT_UNREACHABLE))
            continue

        probe = probe_macro_shared_lift(
            domain,
            shared_lift,
            max_expansions=compile_config.max_probe_expansions,
        )
        if not probe.reachable:
            macro_rejected.append(
                _reject(
                    children,
                    MacroRejectReason.SHARED_LIFT_UNREACHABLE,
                    route_probe_cost=probe.cost,
                )
            )
            continue

        macro = _build_macro_bundle(children, shared_lift, shared_ring)
        macro_normal.append(
            MacroBundleCandidate(
                macro_id=macro.macro_id,
                macro=macro,
                route_probe_cost=probe.cost,
                reachable=True,
            )
        )

    return MacroGenerationResult(
        macro_normal=tuple(macro_normal),
        macro_rejected=tuple(macro_rejected),
    )


__all__ = [
    "MacroCompileConfig",
    "MacroGenerationResult",
    "RejectedMacroBundle",
    "compile_macros",
]
