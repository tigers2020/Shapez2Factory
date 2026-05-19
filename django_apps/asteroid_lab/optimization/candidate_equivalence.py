"""Phase H — candidate equivalence key and dedupe (PR3)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import Direction, TransportKind


@dataclass(frozen=True, slots=True)
class CandidateEquivalenceKey:
    occupied_cells: frozenset[Coord]
    route_probe_start: Coord
    output_dir: Direction
    transport_kind: TransportKind
    base_throughput: int
    topology_signature: str


def equivalence_key_for_candidate(candidate: GeneCandidate) -> CandidateEquivalenceKey:
    return CandidateEquivalenceKey(
        occupied_cells=candidate.occupied_cells,
        route_probe_start=candidate.route_probe_start,
        output_dir=candidate.output_dir,
        transport_kind=candidate.transport_kind,
        base_throughput=candidate.base_throughput,
        topology_signature=candidate.topology_signature,
    )


def dedupe_gene_candidates(
    candidates: tuple[GeneCandidate, ...],
) -> tuple[GeneCandidate, ...]:
    """Keep first candidate per equivalence key (lowest ``candidate_id`` wins)."""

    best_by_key: dict[CandidateEquivalenceKey, GeneCandidate] = {}
    for candidate in candidates:
        key = equivalence_key_for_candidate(candidate)
        existing = best_by_key.get(key)
        if existing is None or candidate.candidate_id < existing.candidate_id:
            best_by_key[key] = candidate

    # Preserve first-seen key order from input enumeration, not sorted keys.
    seen_keys: set[CandidateEquivalenceKey] = set()
    ordered: list[GeneCandidate] = []
    for candidate in candidates:
        key = equivalence_key_for_candidate(candidate)
        if key in seen_keys:
            continue
        if best_by_key.get(key) is candidate:
            ordered.append(candidate)
            seen_keys.add(key)
    return tuple(ordered)
