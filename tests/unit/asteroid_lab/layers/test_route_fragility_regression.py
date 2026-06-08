"""Sequence 10B route fragility regression pack (named fixtures only)."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.penalty_mode import PenaltyMode
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement import (
    beam_selector,
    candidate_gen,
    commit_finalize,
    commit_reprobe,
)
from tests.unit.asteroid_lab.layers.fixtures.narrow_corridor_maps import (
    S1_ANCHOR_A,
    S1_ANCHOR_B,
    s1_probe_vs_commit_catalog,
    s1_probe_vs_commit_complete_map,
    s1_probe_vs_commit_exterior_plan,
    s2_future_expansion_catalog,
    s2_future_expansion_complete_map,
    s2_future_expansion_exterior_plan,
)


@dataclass(frozen=True, slots=True)
class _FragilityObservation:
    committed_count: int
    probe_vs_commit_drops: int
    shared_corridor_pressure: int
    total_throughput: int
    future_expansion_cells: int


def _observe_s2(mode: PenaltyMode) -> _FragilityObservation:
    complete_map = s2_future_expansion_complete_map()
    exterior_plan = s2_future_expansion_exterior_plan()
    pool = candidate_gen.generate_candidates(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        genetic_sample_seeds=s2_future_expansion_catalog(),
    ).normal_candidates
    commit_ctx = commit_reprobe.build_commit_reprobe_context(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert commit_ctx is not None
    rim_anchors = frozenset({(1, 1), (1, 3)})
    selection = beam_selector.select_bundles(
        pool,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchors,
        penalty_mode=mode,
    )
    finalized = commit_finalize.finalize_selection(
        selected=selection.selected,
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    expansion_cells = sum(
        max(0, len(probed.candidate.mining_occupied_cells) - 1) for probed in selection.selected
    )
    return _FragilityObservation(
        committed_count=len(finalized.committed_placements),
        probe_vs_commit_drops=len(finalized.rejected_attempts),
        shared_corridor_pressure=sum(f.shared_corridor_cells for f in selection.fitness),
        total_throughput=selection.total_throughput,
        future_expansion_cells=expansion_cells,
    )


def test_future_expansion_penalty_regression() -> None:
    """S2: high-TF west extension vs conservative m0e picks on named fixture."""

    standard = _observe_s2(PenaltyMode.STANDARD)
    conservative = _observe_s2(PenaltyMode.CONSERVATIVE)
    assert standard.committed_count == conservative.committed_count == 2
    assert conservative.probe_vs_commit_drops <= standard.probe_vs_commit_drops
    assert conservative.total_throughput <= standard.total_throughput
    assert conservative.future_expansion_cells < standard.future_expansion_cells
    assert (
        conservative.shared_corridor_pressure < standard.shared_corridor_pressure
        or conservative.probe_vs_commit_drops < standard.probe_vs_commit_drops
        or conservative.future_expansion_cells < standard.future_expansion_cells
    )


def test_route_fragility_reservation_starvation_fixture() -> None:
    """Named S1 fixture: stale probe order with blk reservation causes finalize drop."""

    complete_map = s1_probe_vs_commit_complete_map()
    exterior_plan = s1_probe_vs_commit_exterior_plan()
    pool = candidate_gen.generate_candidates(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        genetic_sample_seeds=s1_probe_vs_commit_catalog(),
    ).normal_candidates
    candidate_a = next(
        c for c in pool if c.candidate.anchor_coord == S1_ANCHOR_A and c.candidate.gene_key == "blk"
    )
    candidate_b = next(
        c for c in pool if c.candidate.anchor_coord == S1_ANCHOR_B and c.candidate.gene_key == "m0e"
    )
    b_alone = commit_finalize.finalize_selection(
        selected=(candidate_b,),
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    a_then_b = commit_finalize.finalize_selection(
        selected=(candidate_a, candidate_b),
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert len(b_alone.committed_placements) == 1
    assert len(a_then_b.committed_placements) == 1
    assert len(a_then_b.rejected_attempts) == 1
