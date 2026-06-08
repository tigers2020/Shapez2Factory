"""Sequence 10A narrow corridor regression pack (S1, S3, S4)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import RimGreedyRejectReason
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.beam_selector import (
    FitnessBreakdown,
    select_bundles,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.candidate_gen import (
    generate_candidates,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_finalize import (
    finalize_selection,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_reprobe import (
    build_commit_reprobe_context,
)
from tests.unit.asteroid_lab.layers.fixtures.narrow_corridor_maps import (
    S1_ANCHOR_A,
    S1_ANCHOR_B,
    s1_probe_vs_commit_catalog,
    s1_probe_vs_commit_complete_map,
    s1_probe_vs_commit_exterior_plan,
    s3_corridor_sharing_catalog,
    s3_corridor_sharing_complete_map,
    s3_corridor_sharing_exterior_plan,
    s4_dual_transport_catalog,
    s4_dual_transport_complete_map,
    s4_dual_transport_exterior_plan,
)


def _pick(
    pool: tuple[RouteProbedBundleCandidate, ...],
    *,
    anchor: tuple[int, int],
    gene_key: str,
) -> RouteProbedBundleCandidate:
    return next(
        c
        for c in pool
        if c.candidate.anchor_coord == anchor and c.candidate.gene_key == gene_key
    )


def test_narrow_corridor_probe_vs_commit_regression() -> None:
    """S1: both pool-feasible at probe time; B alone commits; A then B rejects B after reservation."""

    complete_map = s1_probe_vs_commit_complete_map()
    exterior_plan = s1_probe_vs_commit_exterior_plan()
    catalog = s1_probe_vs_commit_catalog()
    pool = generate_candidates(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        genetic_sample_seeds=catalog,
    ).normal_candidates
    candidate_a = _pick(pool, anchor=S1_ANCHOR_A, gene_key="blk")
    candidate_b = _pick(pool, anchor=S1_ANCHOR_B, gene_key="m0e")
    assert candidate_a.route_probe_status.value == "succeeded"
    assert candidate_b.route_probe_status.value == "succeeded"

    b_alone = finalize_selection(
        selected=(candidate_b,),
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert len(b_alone.committed_placements) == 1
    assert b_alone.committed_placements[0].anchor == S1_ANCHOR_B

    a_then_b = finalize_selection(
        selected=(candidate_a, candidate_b),
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert len(a_then_b.committed_placements) == 1
    assert a_then_b.committed_placements[0].anchor == S1_ANCHOR_A
    assert len(a_then_b.rejected_attempts) == 1
    reject = a_then_b.rejected_attempts[0]
    assert reject.anchor == S1_ANCHOR_B
    assert reject.seed_id == "m0e"
    assert reject.reason in {
        RimGreedyRejectReason.EQUIPMENT_COLLISION,
        RimGreedyRejectReason.DPS_UNREACHABLE,
        RimGreedyRejectReason.ROUTE_CROSSES_HARD_BLOCKER,
    }


def test_shared_corridor_pressure_regression() -> None:
    """S3: shared void corridor is soft pressure, not a hard reject under STANDARD beam."""

    complete_map = s3_corridor_sharing_complete_map()
    exterior_plan = s3_corridor_sharing_exterior_plan()
    pool = generate_candidates(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        genetic_sample_seeds=s3_corridor_sharing_catalog(),
    ).normal_candidates
    by_anchor = {(1, 1): _pick(pool, anchor=(1, 1), gene_key="m0e"), (1, 3): _pick(pool, anchor=(1, 3), gene_key="m0e")}
    commit_ctx = build_commit_reprobe_context(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert commit_ctx is not None
    result = select_bundles(
        (by_anchor[(1, 1)], by_anchor[(1, 3)]),
        commit_ctx=commit_ctx,
    )
    assert {p.candidate.anchor_coord for p in result.selected} == {(1, 1), (1, 3)}
    assert result.rejected_overlap_count == 0
    shared = [f for f in result.fitness if f.shared_corridor_cells > 0]
    assert shared, "expected shared corridor pressure on the second bundle"
    assert all(isinstance(f, FitnessBreakdown) for f in result.fitness)


def test_trunk_sharing_penalty_regression() -> None:
    """S3 variant: two miners may finalize through the same exterior merge trunk."""

    complete_map = s3_corridor_sharing_complete_map()
    exterior_plan = s3_corridor_sharing_exterior_plan()
    pool = generate_candidates(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        genetic_sample_seeds=s3_corridor_sharing_catalog(),
    ).normal_candidates
    north = _pick(pool, anchor=(1, 1), gene_key="m0e")
    south = _pick(pool, anchor=(1, 3), gene_key="m0e")
    finalized = finalize_selection(
        selected=(north, south),
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert len(finalized.committed_placements) == 2
    goals = {p.route_probe_path[-1] for p in finalized.committed_placements}
    assert len(goals) == 1


def test_transport_kind_corridor_conflict_regression() -> None:
    """S4: shape belt and fluid pipe probes use separate transport kinds (no cross-kind merge)."""

    pool = generate_candidates(
        complete_map=s4_dual_transport_complete_map(),
        exterior_plan=s4_dual_transport_exterior_plan(),
        genetic_sample_seeds=s4_dual_transport_catalog(),
    ).normal_candidates
    shape_probe = _pick(pool, anchor=(3, 1), gene_key="shape_m0e")
    fluid_probe = _pick(pool, anchor=(3, 3), gene_key="fluid_m0e")
    assert shape_probe.route_probe_result is not None
    assert fluid_probe.route_probe_result is not None
    assert shape_probe.route_probe_result.transport_kind == TransportKind.SHAPE_BELT
    assert fluid_probe.route_probe_result.transport_kind == TransportKind.FLUID_PIPE
    assert shape_probe.route_probe_result.goal_coord != fluid_probe.route_probe_result.goal_coord
