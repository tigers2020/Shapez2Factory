"""Layer 03 Phase C1 — deterministic beam selector over the route-feasible normal pool.

Spec Phase C1 (v2 MVP): pick a non-conflicting subset of the route-feasible normal pool
that maximizes routed throughput minus predictive penalties. Equipment overlap is a HARD
constraint (two bundles may never share an equipment cell); shared route corridors are a
soft penalty (``shared corridor pressure``), and per-candidate ``route_cost`` is a soft
penalty too. The selector is fully deterministic: candidates are pre-sorted by a stable
fitness key (independent of input order), a fixed-width beam explores add/skip branches,
and ties break on the selected ``candidate_id`` sequence.

This is Phase C1 only — it does not commit. Commit-time re-probe on the latest route domain
is Phase D. The selection order is derived from fitness/conflict state, never from the raw
D1 enumeration order (spec D2).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

# Fitness weights (integer arithmetic keeps selection deterministic — no float rounding).
# Throughput dominates; route cost and shared-corridor pressure only break near-ties.
_THROUGHPUT_WEIGHT = 1000
_ROUTE_COST_WEIGHT = 1
_CORRIDOR_PRESSURE_WEIGHT = 10
_DEFAULT_BEAM_WIDTH = 16


@dataclass(frozen=True, slots=True)
class FitnessBreakdown:
    """Per-selected-candidate fitness contribution, recorded at the time it was added."""

    candidate_id: str
    throughput_factor: int
    route_cost: int
    shared_corridor_cells: int
    net_score: int


@dataclass(frozen=True, slots=True)
class BeamSelectionResult:
    """Outcome of the Phase C1 beam selection (no commit)."""

    selected: tuple[RouteProbedBundleCandidate, ...]
    fitness: tuple[FitnessBreakdown, ...]
    total_throughput: int
    total_net_score: int
    rejected_overlap_count: int


@dataclass(frozen=True, slots=True)
class _BeamState:
    occupied: frozenset[Coord]
    corridor: frozenset[Coord]
    selected: tuple[RouteProbedBundleCandidate, ...] = ()
    fitness: tuple[FitnessBreakdown, ...] = ()
    total_throughput: int = 0
    total_net_score: int = 0
    selected_ids: tuple[str, ...] = field(default=())

    def rank_key(self) -> tuple[int, int, tuple[str, ...]]:
        # Higher net score first, then higher throughput, then lexicographic id sequence
        # so equal-score states resolve deterministically regardless of input order.
        return (-self.total_net_score, -self.total_throughput, self.selected_ids)


def _equipment_cells(probed: RouteProbedBundleCandidate) -> frozenset[Coord]:
    cand = probed.candidate
    return cand.mining_occupied_cells | cand.transport_stub_cells


def _corridor_cells(probed: RouteProbedBundleCandidate) -> frozenset[Coord]:
    result = probed.route_probe_result
    if result is None:
        return frozenset()
    return frozenset(result.path_coords) - _equipment_cells(probed)


def _route_cost(probed: RouteProbedBundleCandidate) -> int:
    result = probed.route_probe_result
    return 0 if result is None else result.route_cost


def _fitness_sort_key(probed: RouteProbedBundleCandidate) -> tuple[int, int, str]:
    # Deterministic seed order: highest throughput first, then cheapest route, then id.
    return (-probed.candidate.throughput_factor, _route_cost(probed), probed.candidate.candidate_id)


def _extend(
    state: _BeamState,
    probed: RouteProbedBundleCandidate,
    *,
    equipment: frozenset[Coord],
    corridor: frozenset[Coord],
) -> _BeamState:
    shared = len(state.corridor & corridor)
    route_cost = _route_cost(probed)
    throughput = probed.candidate.throughput_factor
    net = (
        throughput * _THROUGHPUT_WEIGHT
        - route_cost * _ROUTE_COST_WEIGHT
        - shared * _CORRIDOR_PRESSURE_WEIGHT
    )
    breakdown = FitnessBreakdown(
        candidate_id=probed.candidate.candidate_id,
        throughput_factor=throughput,
        route_cost=route_cost,
        shared_corridor_cells=shared,
        net_score=net,
    )
    return replace(
        state,
        occupied=state.occupied | equipment,
        corridor=state.corridor | corridor,
        selected=(*state.selected, probed),
        fitness=(*state.fitness, breakdown),
        total_throughput=state.total_throughput + throughput,
        total_net_score=state.total_net_score + net,
        selected_ids=(*state.selected_ids, probed.candidate.candidate_id),
    )


def select_bundles(
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    *,
    beam_width: int = _DEFAULT_BEAM_WIDTH,
) -> BeamSelectionResult:
    """Deterministically select a non-conflicting, throughput-maximizing subset (Phase C1).

    Equipment overlap is a hard constraint; shared route corridors and route cost are soft
    penalties folded into the fitness score. Returns the chosen bundles in selection order
    (derived from fitness/conflict state, not the D1 enumeration order — spec D2).
    """

    ordered = sorted(normal_candidates, key=_fitness_sort_key)
    beam: list[_BeamState] = [_BeamState(occupied=frozenset(), corridor=frozenset())]

    for probed in ordered:
        equipment = _equipment_cells(probed)
        corridor = _corridor_cells(probed)
        next_beam: list[_BeamState] = []
        for state in beam:
            next_beam.append(state)  # skip branch
            if not (state.occupied & equipment):  # add branch (hard overlap forbidden)
                next_beam.append(_extend(state, probed, equipment=equipment, corridor=corridor))
        next_beam.sort(key=_BeamState.rank_key)
        beam = next_beam[:beam_width]

    best = min(beam, key=_BeamState.rank_key)
    selected_equipment = best.occupied
    selected_ids = set(best.selected_ids)
    rejected_overlap = sum(
        1
        for probed in ordered
        if probed.candidate.candidate_id not in selected_ids
        and bool(_equipment_cells(probed) & selected_equipment)
    )
    return BeamSelectionResult(
        selected=best.selected,
        fitness=best.fitness,
        total_throughput=best.total_throughput,
        total_net_score=best.total_net_score,
        rejected_overlap_count=rejected_overlap,
    )


__all__ = [
    "BeamSelectionResult",
    "FitnessBreakdown",
    "select_bundles",
]
