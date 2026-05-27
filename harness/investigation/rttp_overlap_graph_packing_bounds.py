"""Read-only overlap graph packing bounds (P1-ELCP-RF-B1 Phase 0; not solver input)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.equivalence import dedupe_candidates
from django_apps.asteroid_lab.optimization.selection.greedy_regret import select_genome
from django_apps.asteroid_lab.optimization.selection.overlap_graph import (
    OverlapPackingBounds,
    UpperBoundMethod,
    build_overlap_adjacency,
    compute_overlap_packing_bounds,
    compute_target_floor,
    count_undirected_edges,
    phase0_is_no_go,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


@dataclass(frozen=True, slots=True)
class OverlapPackingBoundsReport:
    vertex_count: int
    edge_count: int
    connected_component_count: int
    greedy_regret_baseline: int
    best_known_independent_set_size: int
    exact_mis_size: int | None
    upper_bound: int
    upper_bound_method: str
    component_sizes: tuple[int, ...]
    exact_mis_component_count: int
    heuristic_mis_component_count: int
    chromatic_upper_bound_sum: int
    target_floor: int
    phase0_verdict: str
    fot_conflict_edge_count: int

    @classmethod
    def from_bounds(
        cls,
        bounds: OverlapPackingBounds,
        *,
        target_floor: int,
        phase0_verdict: str,
        fot_conflict_edge_count: int,
    ) -> OverlapPackingBoundsReport:
        return cls(
            vertex_count=bounds.vertex_count,
            edge_count=bounds.edge_count,
            connected_component_count=bounds.connected_component_count,
            greedy_regret_baseline=bounds.greedy_regret_baseline,
            best_known_independent_set_size=bounds.best_known_independent_set_size,
            exact_mis_size=bounds.exact_mis_size,
            upper_bound=bounds.upper_bound,
            upper_bound_method=bounds.upper_bound_method.value,
            component_sizes=bounds.component_sizes,
            exact_mis_component_count=bounds.exact_mis_component_count,
            heuristic_mis_component_count=bounds.heuristic_mis_component_count,
            chromatic_upper_bound_sum=bounds.chromatic_upper_bound_sum,
            target_floor=target_floor,
            phase0_verdict=phase0_verdict,
            fot_conflict_edge_count=fot_conflict_edge_count,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertex_count": self.vertex_count,
            "edge_count": self.edge_count,
            "connected_component_count": self.connected_component_count,
            "greedy_regret_baseline": self.greedy_regret_baseline,
            "best_known_independent_set_size": self.best_known_independent_set_size,
            "exact_mis_size": self.exact_mis_size,
            "upper_bound": self.upper_bound,
            "upper_bound_method": self.upper_bound_method,
            "component_sizes": list(self.component_sizes),
            "exact_mis_component_count": self.exact_mis_component_count,
            "heuristic_mis_component_count": self.heuristic_mis_component_count,
            "chromatic_upper_bound_sum": self.chromatic_upper_bound_sum,
            "target_floor": self.target_floor,
            "phase0_verdict": self.phase0_verdict,
            "fot_conflict_edge_count": self.fot_conflict_edge_count,
        }


def count_fot_conflict_edges(candidates: Sequence[BundleCandidate]) -> int:
    pool = tuple(candidates)
    count = 0
    for left_index, left in enumerate(pool):
        left_fot = fixed_output_transport_cell(left)
        for right in pool[left_index + 1 :]:
            right_fot = fixed_output_transport_cell(right)
            if left.occupied_cells & {right_fot}:
                count += 1
            if right.occupied_cells & {left_fot}:
                count += 1
    return count


def build_overlap_packing_bounds_report(
    *,
    normal_candidates: Sequence[BundleCandidate],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
) -> OverlapPackingBoundsReport:
    pool = dedupe_candidates(tuple(normal_candidates))
    baseline_genome = select_genome(pool, skeleton, inp, goal_count=goal_count)
    greedy_regret_baseline = len(baseline_genome.commit_order)
    bounds = compute_overlap_packing_bounds(
        pool,
        greedy_regret_baseline=greedy_regret_baseline,
    )
    target_floor = compute_target_floor(bounds.best_known_independent_set_size)
    verdict = (
        "NO_GO"
        if phase0_is_no_go(
            best_known_independent_set_size=bounds.best_known_independent_set_size,
            greedy_regret_baseline=greedy_regret_baseline,
        )
        else "GO"
    )
    adj = build_overlap_adjacency(pool)
    _ = count_undirected_edges(adj)
    fot_edges = count_fot_conflict_edges(pool)
    if bounds.upper_bound_method is UpperBoundMethod.TRIVIAL_VERTEX_COUNT:
        msg = "trivial_vertex_count upper bound is forbidden for B1 Phase 0"
        raise ValueError(msg)
    return OverlapPackingBoundsReport.from_bounds(
        bounds,
        target_floor=target_floor,
        phase0_verdict=verdict,
        fot_conflict_edge_count=fot_edges,
    )


__all__ = [
    "OverlapPackingBoundsReport",
    "build_overlap_packing_bounds_report",
    "count_fot_conflict_edges",
]
