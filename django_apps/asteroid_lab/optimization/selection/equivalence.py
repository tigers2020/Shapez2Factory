"""Candidate equivalence dedupe for RTTP Layer 3 (PR-4)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


@dataclass(frozen=True, slots=True)
class CandidateEquivalenceKey:
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: str
    transport_kind: TransportKind
    base_throughput: int
    topology_signature: tuple[str, Coord]


def equivalence_key(candidate: BundleCandidate) -> CandidateEquivalenceKey:
    return CandidateEquivalenceKey(
        occupied_cells=candidate.occupied_cells,
        output_stub=candidate.output_stub,
        output_dir=candidate.output_dir,
        transport_kind=candidate.transport_kind,
        base_throughput=candidate.throughput_factor,
        topology_signature=(candidate.pattern.pattern_id, candidate.anchor_coord),
    )


def dedupe_candidates(
    candidates: tuple[BundleCandidate, ...],
) -> tuple[BundleCandidate, ...]:
    """Keep lowest ``candidate_id`` per equivalence key."""

    best_by_key: dict[CandidateEquivalenceKey, BundleCandidate] = {}
    for candidate in candidates:
        key = equivalence_key(candidate)
        existing = best_by_key.get(key)
        if existing is None or candidate.candidate_id < existing.candidate_id:
            best_by_key[key] = candidate
    return tuple(sorted(best_by_key.values(), key=lambda item: item.candidate_id))


__all__ = ["CandidateEquivalenceKey", "dedupe_candidates", "equivalence_key"]
