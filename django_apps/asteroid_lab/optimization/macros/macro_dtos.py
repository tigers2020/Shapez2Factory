"""MacroBundleT3 DTOs for RTTP v1 (PR-A — types only, no compiler)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord


def _coord_json(coord: Coord) -> list[int]:
    return [coord[0], coord[1]]


def _canonical_coord_set(cells: frozenset[Coord]) -> list[list[int]]:
    return [_coord_json(c) for c in sorted(cells)]


def canonical_shared_lift_stub_plan_json(plan: SharedLiftStubPlan) -> str:
    payload = {
        "lift_column_coords": _canonical_coord_set(plan.lift_column_coords),
        "reserved_route_cells": _canonical_coord_set(plan.reserved_route_cells),
        "trunk_entry_coord": (
            None if plan.trunk_entry_coord is None else _coord_json(plan.trunk_entry_coord)
        ),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def canonical_shared_ring_port_intent_json(intent: SharedRingPortIntent) -> str:
    payload = {
        "preferred_dir": intent.preferred_dir,
        "primary_ring_port_coord": _coord_json(intent.primary_ring_port_coord),
        "secondary_port_coords": _canonical_coord_set(intent.secondary_port_coords),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def derive_macro_id(
    *,
    child_a_id: str,
    child_b_id: str,
    child_c_id: str,
    shared_lift_stub_plan: SharedLiftStubPlan,
    shared_ring_port_intent: SharedRingPortIntent,
) -> str:
    """Deterministic content-addressed macro id (sorted child ids + canonical shared plans)."""

    lift_json = canonical_shared_lift_stub_plan_json(shared_lift_stub_plan)
    ring_json = canonical_shared_ring_port_intent_json(shared_ring_port_intent)
    payload = {
        "child_ids": sorted((child_a_id, child_b_id, child_c_id)),
        "shared_lift_stub_plan": json.loads(lift_json),
        "shared_ring_port_intent": json.loads(ring_json),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def union_child_occupied_cells(children: tuple[BundleCandidate, ...]) -> frozenset[Coord]:
    """Union of child ``occupied_cells`` (equals disjoint union when valid)."""

    combined: set[Coord] = set()
    for child in children:
        combined.update(child.occupied_cells)
    return frozenset(combined)


def child_occupancy_overlaps(children: tuple[BundleCandidate, ...]) -> bool:
    """True when any two children share an occupied cell (compile-time geometry check)."""

    if len(children) < 2:
        return False
    seen: set[Coord] = set()
    for child in children:
        overlap = seen.intersection(child.occupied_cells)
        if overlap:
            return True
        seen.update(child.occupied_cells)
    return False


@dataclass(frozen=True, slots=True)
class SharedLiftStubPlan:
    """Route-only cells; NOT equipment footprint."""

    lift_column_coords: frozenset[Coord]
    trunk_entry_coord: Coord | None
    reserved_route_cells: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class SharedRingPortIntent:
    """Skeleton-relative; does not add occupied_cells."""

    primary_ring_port_coord: Coord
    preferred_dir: str
    secondary_port_coords: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class MacroBundleT3:
    macro_id: str
    child_a_id: str
    child_b_id: str
    child_c_id: str
    children: tuple[BundleCandidate, ...]
    shared_lift_stub_plan: SharedLiftStubPlan
    shared_ring_port_intent: SharedRingPortIntent
    combined_occupied_cells: frozenset[Coord]
    macro_throughput_factor: int
    topology_signature: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MacroBundleCandidate:
    """One macro row in the macro normal pool (probe fields; compiler in PR-B)."""

    macro_id: str
    macro: MacroBundleT3
    route_probe_cost: int
    reachable: bool


__all__ = [
    "MacroBundleCandidate",
    "MacroBundleT3",
    "SharedLiftStubPlan",
    "SharedRingPortIntent",
    "canonical_shared_lift_stub_plan_json",
    "canonical_shared_ring_port_intent_json",
    "child_occupancy_overlaps",
    "derive_macro_id",
    "union_child_occupied_cells",
]
