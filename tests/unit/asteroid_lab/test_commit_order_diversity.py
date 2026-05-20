"""Commit-order diversity tests (selection interleave before commit)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.commit_order_diversity import (
    diversify_commit_order,
    diversity_bucket_key,
)
from django_apps.asteroid_lab.optimization.enums import Direction, RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult


def _goal(coord: tuple[int, int]) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )


def _candidate(
    *,
    candidate_id: str,
    extractor: tuple[int, int],
    path: tuple[tuple[int, int], ...],
    reached_goal: RouteGoal,
    base_throughput: int = 16,
) -> GeneCandidate:
    probe = RouteProbeResult(
        reachable=True,
        path=path,
        cost=len(path),
        expanded_nodes=1,
        reached_goal=reached_goal,
        goal_priority=reached_goal.priority,
        failure_reason=None,
    )
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id="g",
        topology_signature="sig",
        extractor=extractor,
        extensions=(),
        occupied_cells=frozenset({extractor}),
        route_probe_start=(extractor[0] + 1, extractor[1]),
        fixed_output_transport=(extractor[0] + 1, extractor[1]),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=base_throughput,
        base_score=float(base_throughput),
        route_probe_result=probe,
    )


def test_diversify_commit_order_round_robins_across_anchors() -> None:
    """Same goal + corridor at two anchors: greedy block order → interleaved A/B/A/B."""
    goal = _goal((6, 0))
    corridor = ((1, 0), (6, 0), 6)
    anchor_a = (0, 0)
    anchor_b = (8, 0)
    a1 = _candidate(
        candidate_id="anchor_a:g1",
        extractor=anchor_a,
        path=corridor,
        reached_goal=goal,
    )
    a2 = _candidate(
        candidate_id="anchor_a:g2",
        extractor=anchor_a,
        path=corridor,
        reached_goal=goal,
        base_throughput=12,
    )
    b1 = _candidate(
        candidate_id="anchor_b:g1",
        extractor=anchor_b,
        path=corridor,
        reached_goal=goal,
    )
    b2 = _candidate(
        candidate_id="anchor_b:g2",
        extractor=anchor_b,
        path=corridor,
        reached_goal=goal,
        base_throughput=12,
    )
    by_id = {
        c.candidate_id: c for c in (a1, a2, b1, b2)
    }
    greedy_order = SelectedCandidatePlan(
        ordered_candidate_ids=("anchor_a:g1", "anchor_a:g2", "anchor_b:g1", "anchor_b:g2")
    )

    diversified = diversify_commit_order(greedy_order, by_id)

    assert diversified.ordered_candidate_ids == (
        "anchor_a:g1",
        "anchor_b:g1",
        "anchor_a:g2",
        "anchor_b:g2",
    )


def test_diversify_preserves_multiset_of_candidates() -> None:
    goal = _goal((6, 0))
    corridor = ((1, 0), (6, 0), 6)
    candidates = tuple(
        _candidate(
            candidate_id=f"c{i}",
            extractor=(i * 4, 0),
            path=corridor,
            reached_goal=goal,
        )
        for i in range(4)
    )
    by_id = {c.candidate_id: c for c in candidates}
    original = SelectedCandidatePlan(
        ordered_candidate_ids=tuple(c.candidate_id for c in reversed(candidates))
    )

    diversified = diversify_commit_order(original, by_id)

    assert sorted(diversified.ordered_candidate_ids) == sorted(
        original.ordered_candidate_ids
    )


def test_diversify_reduces_consecutive_same_diversity_bucket() -> None:
    goal = _goal((6, 0))
    corridor = ((1, 0), (6, 0), 6)
    candidates = []
    for anchor_x in (0, 8, 16):
        for gene_idx in range(3):
            candidates.append(
                _candidate(
                    candidate_id=f"{anchor_x}:g{gene_idx}",
                    extractor=(anchor_x, 0),
                    path=corridor,
                    reached_goal=goal,
                    base_throughput=16 - gene_idx,
                )
            )
    by_id = {c.candidate_id: c for c in candidates}
    greedy_order = SelectedCandidatePlan(
        ordered_candidate_ids=tuple(
            f"{anchor_x}:g{gene_idx}"
            for anchor_x in (0, 8, 16)
            for gene_idx in range(3)
        )
    )

    def _consecutive_same_bucket_count(plan: SelectedCandidatePlan) -> int:
        keys = [diversity_bucket_key(by_id[cid]) for cid in plan.ordered_candidate_ids]
        return sum(1 for i in range(len(keys) - 1) if keys[i] == keys[i + 1])

    greedy_runs = _consecutive_same_bucket_count(greedy_order)
    diversified_runs = _consecutive_same_bucket_count(
        diversify_commit_order(greedy_order, by_id)
    )
    assert greedy_runs == 6
    assert diversified_runs == 0
    assert diversified_runs < greedy_runs
