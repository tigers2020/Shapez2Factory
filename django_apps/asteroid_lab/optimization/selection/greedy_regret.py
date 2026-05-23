"""Greedy-regret genome selection for RTTP Layer 3 (PR-4).

v0.1: regret is computed per ``anchor_coord`` (not full ``CandidateEquivalenceKey``).
Selection ``committed_route_cells`` tracks output stubs only; commit uses full paths.
"""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.equivalence import dedupe_candidates
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4_server


@dataclass(frozen=True, slots=True)
class SelectionConfig:
    lambda_regret: float = 1.0
    inlet_fragility_weight: float = 1.0
    fragmentation_weight: float = 200.0
    rim_port_alignment_weight: float = 200.0


@dataclass(frozen=True, slots=True)
class PlacementGenome:
    commit_order: tuple[str, ...]


def _rim_port_alignment(candidate: BundleCandidate, skeleton: RttpSkeleton) -> float:
    for port in skeleton.ring_ports:
        if port.coord != candidate.anchor_coord:
            continue
        if port.preferred_dir == candidate.output_dir:
            return 1.0
    return 0.0


def _fragmentation_penalty(
    candidate: BundleCandidate,
    inp: OptimizationInput,
    committed_occupied: frozenset[Coord],
) -> float:
    remaining = inp.mineable_cells - committed_occupied - candidate.occupied_cells
    if not remaining:
        return 0.0
    isolated = 0
    for cell in remaining:
        if not any(neighbor in remaining for neighbor in neighbors4_server(cell)):
            isolated += 1
    return float(isolated) / float(len(remaining))


def _inlet_fragility(
    candidate: BundleCandidate,
    skeleton: RttpSkeleton,
    committed_route_cells: frozenset[Coord],
) -> float:
    penalty = 0.0
    if candidate.output_stub in skeleton.trunk_mask_cells:
        penalty += 1.0
    if candidate.output_stub in committed_route_cells:
        penalty += 2.0
    return penalty


def _base_score(
    candidate: BundleCandidate,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig,
    committed_occupied: frozenset[Coord],
) -> float:
    return (
        1000.0 * float(candidate.throughput_factor)
        + config.rim_port_alignment_weight * _rim_port_alignment(candidate, skeleton)
        - 30.0 * float(candidate.route_probe_cost)
        - config.fragmentation_weight * _fragmentation_penalty(candidate, inp, committed_occupied)
    )


def _regret_scores(
    pool: tuple[BundleCandidate, ...],
    base_scores: dict[str, float],
) -> dict[str, float]:
    by_anchor: dict[Coord, list[BundleCandidate]] = {}
    for candidate in pool:
        by_anchor.setdefault(candidate.anchor_coord, []).append(candidate)

    regrets: dict[str, float] = {}
    for group in by_anchor.values():
        ordered = sorted(
            group,
            key=lambda item: base_scores[item.candidate_id],
            reverse=True,
        )
        if len(ordered) == 1:
            regrets[ordered[0].candidate_id] = 0.0
            continue
        second_best = base_scores[ordered[1].candidate_id]
        for candidate in ordered:
            regrets[candidate.candidate_id] = base_scores[candidate.candidate_id] - second_best
    return regrets


def _priority(
    candidate: BundleCandidate,
    *,
    base_score: float,
    regret: float,
    skeleton: RttpSkeleton,
    committed_route_cells: frozenset[Coord],
    config: SelectionConfig,
) -> float:
    inlet = _inlet_fragility(candidate, skeleton, committed_route_cells)
    return base_score + config.lambda_regret * regret - config.inlet_fragility_weight * inlet


def _overlaps(candidate: BundleCandidate, occupied: frozenset[Coord]) -> bool:
    return bool(candidate.occupied_cells & occupied)


def select_genome(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig | None = None,
) -> PlacementGenome:
    """Greedy-regret selection; ``commit_order`` follows pick order, not rim scan."""

    resolved = config if config is not None else SelectionConfig()
    pool = list(dedupe_candidates(normal_candidates))
    commit_order: list[str] = []
    committed_occupied: set[Coord] = set()
    committed_route_cells: set[Coord] = set()
    goal_count = max(0, skeleton.capacity_goals)

    while pool and len(commit_order) < goal_count:
        base_scores = {
            candidate.candidate_id: _base_score(
                candidate,
                skeleton,
                inp,
                config=resolved,
                committed_occupied=frozenset(committed_occupied),
            )
            for candidate in pool
        }
        regrets = _regret_scores(tuple(pool), base_scores)

        best = max(
            pool,
            key=lambda candidate: (
                _priority(
                    candidate,
                    base_score=base_scores[candidate.candidate_id],
                    regret=regrets[candidate.candidate_id],
                    skeleton=skeleton,
                    committed_route_cells=frozenset(committed_route_cells),
                    config=resolved,
                ),
                -pool.index(candidate),
            ),
        )
        commit_order.append(best.candidate_id)
        committed_occupied.update(best.occupied_cells)
        committed_route_cells.add(best.output_stub)
        pool = [
            candidate
            for candidate in pool
            if candidate.candidate_id != best.candidate_id
            and not _overlaps(candidate, frozenset(committed_occupied))
        ]

    return PlacementGenome(commit_order=tuple(commit_order))


__all__ = ["PlacementGenome", "SelectionConfig", "select_genome"]
