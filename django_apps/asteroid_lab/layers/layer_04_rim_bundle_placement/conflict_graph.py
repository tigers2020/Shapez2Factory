"""Overlap conflict graph and connected components for L4 v2."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def occupied_cells_for_entry(entry: RouteProbedBundleCandidate) -> frozenset[Coord]:
    candidate = entry.candidate
    return candidate.mining_occupied_cells | candidate.transport_stub_cells


def _component_sort_key(
    entries: tuple[RouteProbedBundleCandidate, ...],
) -> tuple[int, int, str]:
    anchor_ys = [e.candidate.anchor_coord[1] for e in entries]
    anchor_xs = [e.candidate.anchor_coord[0] for e in entries]
    candidate_ids = [e.candidate.candidate_id for e in entries]
    return (min(anchor_ys), min(anchor_xs), min(candidate_ids))


@dataclass(frozen=True, slots=True)
class ConflictComponent:
    component_id: str
    component_sort_key: tuple[int, int, str]
    entries: tuple[RouteProbedBundleCandidate, ...]

    @property
    def node_count(self) -> int:
        return len(self.entries)


def build_conflict_components(
    entries: tuple[RouteProbedBundleCandidate, ...],
) -> tuple[ConflictComponent, ...]:
    """Partition entries into overlap connected components (deterministic order)."""

    n = len(entries)
    if n == 0:
        return ()

    occupied = [occupied_cells_for_entry(e) for e in entries]
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            if occupied[i] & occupied[j]:
                union(i, j)

    groups: dict[int, list[RouteProbedBundleCandidate]] = {}
    for idx, entry in enumerate(entries):
        root = find(idx)
        groups.setdefault(root, []).append(entry)

    raw_components: list[tuple[tuple[int, int, str], tuple[RouteProbedBundleCandidate, ...]]] = []
    for group_entries in groups.values():
        ordered = tuple(
            sorted(group_entries, key=lambda e: e.candidate.candidate_id),
        )
        raw_components.append((_component_sort_key(ordered), ordered))

    raw_components.sort(key=lambda item: item[0])

    return tuple(
        ConflictComponent(
            component_id=f"component_{ordinal:04d}",
            component_sort_key=sort_key,
            entries=component_entries,
        )
        for ordinal, (sort_key, component_entries) in enumerate(raw_components)
    )


__all__ = [
    "ConflictComponent",
    "build_conflict_components",
    "occupied_cells_for_entry",
]
