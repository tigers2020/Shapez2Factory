"""Layer 03 Phase C1 ??deterministic beam selector over the route-feasible normal pool.

Spec Phase C1 (v2 MVP): pick a non-conflicting subset of the route-feasible normal pool
that maximizes routed throughput minus predictive penalties. Equipment overlap is a HARD
constraint (two bundles may never share an equipment cell); shared route corridors are a
soft penalty (``shared corridor pressure``), and per-candidate ``route_cost`` is a soft
penalty too. The selector is fully deterministic: candidates are pre-sorted by a stable
fitness key (independent of input order), a fixed-width beam explores add/skip branches,
and ties break on the selected ``candidate_id`` sequence.

This is Phase C1 only ??it does not commit. Commit-time re-probe on the latest route domain
is Phase D. The selection order is derived from fitness/conflict state, never from the raw
D1 enumeration order (spec D2).
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field, replace

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_reprobe import (  # noqa: E501
    CommitDomainState,
    CommitReprobeContext,
    try_commit_reprobe,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

# Fitness weights (integer arithmetic keeps selection deterministic ??no float rounding).
# Throughput dominates; route cost and shared-corridor pressure only break near-ties.
_THROUGHPUT_WEIGHT = 1000
_ROUTE_COST_WEIGHT = 1
_CORRIDOR_PRESSURE_WEIGHT = 10
_DEFAULT_BEAM_WIDTH = 16
_DEFAULT_MIN_RIM_ANCHOR_FILL_RATIO = 0.95
# Per-anchor commit greedy scans the full normal pool (deterministic anchor order).


def _min_committed_anchor_count(rim_anchor_count: int, min_fill_ratio: float) -> int:
    if rim_anchor_count <= 0:
        return 0
    if min_fill_ratio <= 0:
        return 0
    target = math.ceil(min_fill_ratio * rim_anchor_count)
    return min(rim_anchor_count, max(1, target))


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
    domain: CommitDomainState
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


def _fill_variant_sort_key(probed: RouteProbedBundleCandidate) -> tuple[int, int, int, str]:
    # Fill pass: smallest equipment footprint first to maximize anchor coverage.
    return (
        len(_equipment_cells(probed)),
        probed.candidate.throughput_factor,
        _route_cost(probed),
        probed.candidate.candidate_id,
    )


def _extend(
    state: _BeamState,
    probed: RouteProbedBundleCandidate,
    *,
    equipment: frozenset[Coord],
    corridor: frozenset[Coord],
    domain: CommitDomainState,
) -> _BeamState:
    shared = len(state.domain.corridor & corridor)
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
        domain=domain,
        selected=(*state.selected, probed),
        fitness=(*state.fitness, breakdown),
        total_throughput=state.total_throughput + throughput,
        total_net_score=state.total_net_score + net,
        selected_ids=(*state.selected_ids, probed.candidate.candidate_id),
    )


def _rim_neighbor_count(anchor: Coord, rim_anchor_coords: frozenset[Coord]) -> int:
    x, y = anchor
    return sum(
        1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in rim_anchor_coords
    )


def _respects_rim_platform(
    equipment: frozenset[Coord],
    anchor: Coord,
    rim_anchor_coords: frozenset[Coord],
) -> bool:
    """Gene extensions must not occupy another rim anchor's platform cell."""

    return not ((equipment & rim_anchor_coords) - {anchor})


def _many_neighbor_anchor_order(rim_anchor_coords: frozenset[Coord]) -> tuple[Coord, ...]:
    return tuple(
        sorted(
            rim_anchor_coords,
            key=lambda coord: (-_rim_neighbor_count(coord, rim_anchor_coords), coord),
        )
    )


def _sandwich_anchor_order(
    many_order: tuple[Coord, ...],
    *,
    failed: frozenset[Coord],
) -> tuple[Coord, ...]:
    mid = len(many_order) // 2
    return (
        *many_order[:mid],
        *sorted(failed),
        *(anchor for anchor in many_order[mid:] if anchor not in failed),
    )


def _group_by_anchor(
    ordered: tuple[RouteProbedBundleCandidate, ...],
    *,
    anchor_order: tuple[Coord, ...] | None = None,
) -> tuple[tuple[Coord, tuple[RouteProbedBundleCandidate, ...]], ...]:
    by_anchor: dict[Coord, list[RouteProbedBundleCandidate]] = defaultdict(list)
    for probed in ordered:
        by_anchor[probed.candidate.anchor_coord].append(probed)
    for group in by_anchor.values():
        group.sort(key=_fitness_sort_key)
    if anchor_order is not None:
        return tuple(
            (anchor, tuple(by_anchor[anchor])) for anchor in anchor_order if anchor in by_anchor
        )
    return tuple((anchor, tuple(by_anchor[anchor])) for anchor in sorted(by_anchor.keys()))


def _committed_anchor_count(result: BeamSelectionResult) -> int:
    return len({probed.candidate.anchor_coord for probed in result.selected})


def _rebuild_beam_state_from_selection(
    selected: tuple[RouteProbedBundleCandidate, ...],
    *,
    commit_ctx: CommitReprobeContext,
    rim_anchor_coords: frozenset[Coord],
) -> _BeamState:
    state = _BeamState(domain=CommitDomainState())
    for probed in selected:
        equipment = _equipment_cells(probed)
        anchor = probed.candidate.anchor_coord
        if not _respects_rim_platform(equipment, anchor, rim_anchor_coords):
            continue
        corridor = _corridor_cells(probed)
        if state.domain.occupied & equipment:
            continue
        ok, next_domain, _path = try_commit_reprobe(
            ctx=commit_ctx,
            state=state.domain,
            probed=probed,
        )
        if not ok:
            continue
        state = _extend(
            state,
            probed,
            equipment=equipment,
            corridor=corridor,
            domain=next_domain,
        )
    return state


def _apply_fill_pass_to_result(
    result: BeamSelectionResult,
    ordered: tuple[RouteProbedBundleCandidate, ...],
    *,
    commit_ctx: CommitReprobeContext,
    rim_anchor_coords: frozenset[Coord],
    min_fill_ratio: float,
) -> BeamSelectionResult:
    state = _rebuild_beam_state_from_selection(
        result.selected,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchor_coords,
    )
    filled = _greedy_fill_remaining_anchors(
        state,
        ordered,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchor_coords,
        min_fill_ratio=min_fill_ratio,
    )
    return _finalize_selection_result(state=filled, ordered=ordered)


def _pick_best_rim_commit_selection(
    left: BeamSelectionResult,
    right: BeamSelectionResult,
    *,
    rim_anchor_count: int,
    min_fill_ratio: float,
) -> BeamSelectionResult:
    target = _min_committed_anchor_count(rim_anchor_count, min_fill_ratio)
    left_fill = _committed_anchor_count(left)
    right_fill = _committed_anchor_count(right)
    left_met = left_fill >= target
    right_met = right_fill >= target
    if left_met != right_met:
        return left if left_met else right
    if left_met and right_met and left_fill != right_fill:
        return left if left_fill > right_fill else right
    return _pick_higher_throughput(left, right)


def _finalize_selection_result(
    *,
    state: _BeamState,
    ordered: tuple[RouteProbedBundleCandidate, ...],
) -> BeamSelectionResult:
    selected_equipment = state.domain.occupied
    selected_ids = set(state.selected_ids)
    rejected_overlap = sum(
        1
        for probed in ordered
        if probed.candidate.candidate_id not in selected_ids
        and bool(_equipment_cells(probed) & selected_equipment)
    )
    return BeamSelectionResult(
        selected=state.selected,
        fitness=state.fitness,
        total_throughput=state.total_throughput,
        total_net_score=state.total_net_score,
        rejected_overlap_count=rejected_overlap,
    )


def _select_bundles_commit_greedy(
    ordered: tuple[RouteProbedBundleCandidate, ...],
    *,
    commit_ctx: CommitReprobeContext,
    rim_anchor_coords: frozenset[Coord] | None = None,
    one_per_anchor: bool = False,
) -> BeamSelectionResult:
    """Global greedy under Phase D reprobe (throughput-first; full pool)."""

    state = _BeamState(domain=CommitDomainState())
    committed_anchors: set[Coord] = set()
    for probed in ordered:
        anchor = probed.candidate.anchor_coord
        if one_per_anchor and anchor in committed_anchors:
            continue
        equipment = _equipment_cells(probed)
        if rim_anchor_coords is not None and not _respects_rim_platform(
            equipment, anchor, rim_anchor_coords
        ):
            continue
        corridor = _corridor_cells(probed)
        if state.domain.occupied & equipment:
            continue
        ok, next_domain, _path = try_commit_reprobe(
            ctx=commit_ctx,
            state=state.domain,
            probed=probed,
        )
        if not ok:
            continue
        committed_anchors.add(anchor)
        state = _extend(
            state,
            probed,
            equipment=equipment,
            corridor=corridor,
            domain=next_domain,
        )
    return _finalize_selection_result(state=state, ordered=ordered)


def _select_bundles_per_anchor_commit_greedy(
    ordered: tuple[RouteProbedBundleCandidate, ...],
    *,
    commit_ctx: CommitReprobeContext,
    rim_anchor_coords: frozenset[Coord] | None = None,
    anchor_order: tuple[Coord, ...] | None = None,
) -> BeamSelectionResult:
    """One commit per rim anchor: best feasible gene variant under Phase D reprobe."""

    state = _BeamState(domain=CommitDomainState())
    for anchor, group in _group_by_anchor(ordered, anchor_order=anchor_order):
        for probed in group:
            equipment = _equipment_cells(probed)
            if rim_anchor_coords is not None and not _respects_rim_platform(
                equipment, anchor, rim_anchor_coords
            ):
                continue
            corridor = _corridor_cells(probed)
            if state.domain.occupied & equipment:
                continue
            ok, next_domain, _path = try_commit_reprobe(
                ctx=commit_ctx,
                state=state.domain,
                probed=probed,
            )
            if not ok:
                continue
            state = _extend(
                state,
                probed,
                equipment=equipment,
                corridor=corridor,
                domain=next_domain,
            )
            break
    return _finalize_selection_result(state=state, ordered=ordered)


def _greedy_fill_remaining_anchors(
    state: _BeamState,
    ordered: tuple[RouteProbedBundleCandidate, ...],
    *,
    commit_ctx: CommitReprobeContext,
    rim_anchor_coords: frozenset[Coord],
    min_fill_ratio: float,
) -> _BeamState:
    """Second pass: place any feasible bundle on unfilled anchors until fill ratio target."""

    target_count = _min_committed_anchor_count(len(rim_anchor_coords), min_fill_ratio)
    if target_count <= 0:
        return state

    def _committed_anchors(current: _BeamState) -> set[Coord]:
        return {probed.candidate.anchor_coord for probed in current.selected}

    if len(_committed_anchors(state)) >= target_count:
        return state

    by_anchor = dict(_group_by_anchor(ordered))
    for anchor in sorted(rim_anchor_coords):
        if len(_committed_anchors(state)) >= target_count:
            break
        if anchor in _committed_anchors(state):
            continue
        group = tuple(sorted(by_anchor.get(anchor, ()), key=_fill_variant_sort_key))
        for probed in group:
            equipment = _equipment_cells(probed)
            if not _respects_rim_platform(equipment, anchor, rim_anchor_coords):
                continue
            if state.domain.occupied & equipment:
                continue
            ok, next_domain, _path = try_commit_reprobe(
                ctx=commit_ctx,
                state=state.domain,
                probed=probed,
            )
            if not ok:
                continue
            corridor = _corridor_cells(probed)
            state = _extend(
                state,
                probed,
                equipment=equipment,
                corridor=corridor,
                domain=next_domain,
            )
            break
    return state


def _select_bundles_rim_platform_commit(
    ordered: tuple[RouteProbedBundleCandidate, ...],
    *,
    commit_ctx: CommitReprobeContext,
    rim_anchor_coords: frozenset[Coord],
    min_rim_anchor_fill_ratio: float = _DEFAULT_MIN_RIM_ANCHOR_FILL_RATIO,
) -> BeamSelectionResult:
    """Rim-platform-aware commit greedy with a second-pass sandwich reorder."""

    many_order = _many_neighbor_anchor_order(rim_anchor_coords)
    first_pass = _select_bundles_per_anchor_commit_greedy(
        ordered,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchor_coords,
        anchor_order=many_order,
    )
    failed = frozenset(rim_anchor_coords) - {
        probed.candidate.anchor_coord for probed in first_pass.selected
    }
    if failed:
        sandwich_order = _sandwich_anchor_order(many_order, failed=failed)
        second_pass = _select_bundles_per_anchor_commit_greedy(
            ordered,
            commit_ctx=commit_ctx,
            rim_anchor_coords=rim_anchor_coords,
            anchor_order=sandwich_order,
        )
        per_anchor = _pick_higher_throughput(first_pass, second_pass)
    else:
        per_anchor = first_pass
    global_greedy = _select_bundles_commit_greedy(
        ordered,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchor_coords,
        one_per_anchor=True,
    )
    per_anchor = _apply_fill_pass_to_result(
        per_anchor,
        ordered,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchor_coords,
        min_fill_ratio=min_rim_anchor_fill_ratio,
    )
    global_greedy = _apply_fill_pass_to_result(
        global_greedy,
        ordered,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchor_coords,
        min_fill_ratio=min_rim_anchor_fill_ratio,
    )
    return _pick_best_rim_commit_selection(
        per_anchor,
        global_greedy,
        rim_anchor_count=len(rim_anchor_coords),
        min_fill_ratio=min_rim_anchor_fill_ratio,
    )


def _pick_higher_throughput(
    left: BeamSelectionResult,
    right: BeamSelectionResult,
) -> BeamSelectionResult:
    if right.total_throughput > left.total_throughput:
        return right
    if left.total_throughput > right.total_throughput:
        return left
    if right.total_net_score > left.total_net_score:
        return right
    if left.total_net_score > right.total_net_score:
        return left
    return left if len(left.selected) <= len(right.selected) else right


def _select_bundles_beam(
    ordered: tuple[RouteProbedBundleCandidate, ...],
    *,
    beam_width: int,
) -> BeamSelectionResult:
    """Classic beam search using isolated Phase B corridors (no commit reprobe)."""

    beam: list[_BeamState] = [_BeamState(domain=CommitDomainState())]

    for probed in ordered:
        equipment = _equipment_cells(probed)
        corridor = _corridor_cells(probed)
        next_beam: list[_BeamState] = []
        for state in beam:
            next_beam.append(state)  # skip branch
            if not (state.domain.occupied & equipment):
                next_beam.append(
                    _extend(
                        state,
                        probed,
                        equipment=equipment,
                        corridor=corridor,
                        domain=CommitDomainState(
                            occupied=state.domain.occupied | equipment,
                            corridor=state.domain.corridor | corridor,
                        ),
                    )
                )
        next_beam.sort(key=_BeamState.rank_key)
        beam = next_beam[:beam_width]

    best = min(beam, key=_BeamState.rank_key)
    selected_equipment = best.domain.occupied
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


def select_bundles(
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    *,
    beam_width: int = _DEFAULT_BEAM_WIDTH,
    commit_ctx: CommitReprobeContext | None = None,
    rim_anchor_coords: frozenset[Coord] | None = None,
    min_rim_anchor_fill_ratio: float = _DEFAULT_MIN_RIM_ANCHOR_FILL_RATIO,
) -> BeamSelectionResult:
    """Deterministically select a non-conflicting, throughput-maximizing subset (Phase C1).

    Equipment overlap is a hard constraint; shared route corridors and route cost are soft
    penalties folded into the fitness score. Returns the chosen bundles in selection order
    (derived from fitness/conflict state, not the D1 enumeration order ??spec D2).

    When ``commit_ctx`` is set, uses per-anchor commit-greedy (Phase-D-aligned) so miners
    on distinct rim anchors can share exterior belt trunks toward the same connector.
    """

    ordered = tuple(sorted(normal_candidates, key=_fitness_sort_key))
    if commit_ctx is not None:
        if rim_anchor_coords is not None:
            return _select_bundles_rim_platform_commit(
                ordered,
                commit_ctx=commit_ctx,
                rim_anchor_coords=rim_anchor_coords,
                min_rim_anchor_fill_ratio=min_rim_anchor_fill_ratio,
            )
        per_anchor = _select_bundles_per_anchor_commit_greedy(ordered, commit_ctx=commit_ctx)
        global_greedy = _select_bundles_commit_greedy(ordered, commit_ctx=commit_ctx)
        return _pick_higher_throughput(per_anchor, global_greedy)
    return _select_bundles_beam(ordered, beam_width=beam_width)


__all__ = [
    "BeamSelectionResult",
    "FitnessBreakdown",
    "select_bundles",
]
