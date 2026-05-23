"""Macro equivalence dedupe for RTTP v1 (PR-C, RTTP-G11)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.macros.macro_dtos import (
    MacroBundleCandidate,
    MacroBundleT3,
    SharedLiftStubPlan,
)
from django_apps.asteroid_lab.optimization.selection.equivalence import (
    CandidateEquivalenceKey,
    equivalence_key,
)


@dataclass(frozen=True, slots=True)
class MacroEquivalenceKey:
    combined_occupied_cells: frozenset[Coord]
    child_equivalence_keys: tuple[CandidateEquivalenceKey, ...]
    shared_lift_signature: tuple[Coord, ...]
    transport_kind: TransportKind
    macro_throughput_factor: int


def _shared_lift_signature(plan: SharedLiftStubPlan) -> tuple[Coord, ...]:
    cells = set(plan.lift_column_coords)
    if plan.trunk_entry_coord is not None:
        cells.add(plan.trunk_entry_coord)
    return tuple(sorted(cells))


def macro_equivalence_key(macro: MacroBundleT3) -> MacroEquivalenceKey:
    child_keys = tuple(equivalence_key(child) for child in macro.children)
    transport_kind = macro.children[0].transport_kind
    return MacroEquivalenceKey(
        combined_occupied_cells=macro.combined_occupied_cells,
        child_equivalence_keys=child_keys,
        shared_lift_signature=_shared_lift_signature(macro.shared_lift_stub_plan),
        transport_kind=transport_kind,
        macro_throughput_factor=macro.macro_throughput_factor,
    )


def dedupe_macros(
    macros: tuple[MacroBundleCandidate, ...],
) -> tuple[MacroBundleCandidate, ...]:
    """Keep lowest ``macro_id`` per macro equivalence key."""

    best_by_key: dict[MacroEquivalenceKey, MacroBundleCandidate] = {}
    for row in macros:
        key = macro_equivalence_key(row.macro)
        existing = best_by_key.get(key)
        if existing is None or row.macro_id < existing.macro_id:
            best_by_key[key] = row
    return tuple(sorted(best_by_key.values(), key=lambda item: item.macro_id))


__all__ = [
    "MacroEquivalenceKey",
    "dedupe_macros",
    "macro_equivalence_key",
]
