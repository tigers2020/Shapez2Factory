"""Bounded local LNS repair after partial commit failure (RTTP Layer 4, PR-5)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneCapacityPlan
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.elcp_commit_guard import (
    is_elcp_incomplete_commit_result,
    retry_may_replace_best,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitResult,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


@dataclass(frozen=True, slots=True)
class LocalLnsConfig:
    radius: int = 3
    max_iters: int = 5


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _conflict_anchors(
    commit_result: CommitResult,
    candidates_by_id: dict[str, BundleCandidate],
) -> tuple[Coord, ...]:
    anchors: list[Coord] = []
    for conflict in commit_result.conflicts:
        candidate = candidates_by_id.get(conflict.candidate_id)
        if candidate is not None:
            anchors.append(candidate.anchor_coord)
    return tuple(anchors)


def _window_bundle_ids(
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    conflict_anchors: tuple[Coord, ...],
    *,
    radius: int,
) -> frozenset[str]:
    if not conflict_anchors:
        return frozenset()
    remove: set[str] = set()
    for candidate_id in genome.commit_order:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            continue
        if any(_manhattan(candidate.anchor_coord, anchor) <= radius for anchor in conflict_anchors):
            remove.add(candidate_id)
    return frozenset(remove)


def run_local_lns(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    commit_result: CommitResult,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    config: LocalLnsConfig | None = None,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None = None,
    route_probe_start_policy: RouteProbeStartPolicy = RouteProbeStartPolicy.OUTPUT_STUB_ONLY,
    resource_kind: str | None = None,
) -> tuple[PlacementGenome, CommitResult]:
    """Repair partial commit failures; only meaningful when ``commit_result.conflicts``."""

    if not commit_result.conflicts:
        return genome, commit_result

    resolved = config if config is not None else LocalLnsConfig()
    best_genome = genome
    best_result = commit_result

    for _ in range(resolved.max_iters):
        conflict_anchors = _conflict_anchors(best_result, candidates_by_id)
        if not conflict_anchors:
            break

        window_ids = _window_bundle_ids(
            best_genome,
            candidates_by_id,
            conflict_anchors,
            radius=resolved.radius,
        )
        kept_ids = [cid for cid in best_genome.commit_order if cid not in window_ids]
        regen = generate_candidates(inp, skeleton, policy=policy)
        regen_by_id = {item.candidate_id: item for item in regen.normal_candidates}
        merged: dict[str, BundleCandidate] = {
            cid: candidates_by_id[cid] for cid in kept_ids if cid in candidates_by_id
        }
        merged.update(regen_by_id)
        pool = tuple(merged.values())
        if not pool:
            break

        candidate_genome = select_genome(pool, skeleton, inp)
        ordered = kept_ids + [cid for cid in candidate_genome.commit_order if cid not in kept_ids]
        retry_genome = PlacementGenome(commit_order=tuple(ordered))
        domain = initial_commit_domain(skeleton, inp)
        retry_result = incremental_commit(
            retry_genome,
            merged,
            inp,
            skeleton,
            domain=domain,
            route_probe_start_policy=route_probe_start_policy,
            exterior_lane_plan=exterior_lane_plan,
            resource_kind=resource_kind,
        )

        if retry_may_replace_best(
            exterior_lane_plan=exterior_lane_plan,
            best_result=best_result,
            retry_result=retry_result,
        ):
            best_genome = retry_genome
            best_result = retry_result
            candidates_by_id.clear()
            candidates_by_id.update(merged)

        if not retry_result.conflicts:
            if is_elcp_incomplete_commit_result(
                exterior_lane_plan=exterior_lane_plan,
                commit_result=retry_result,
            ):
                continue
            candidates_by_id.clear()
            candidates_by_id.update(merged)
            return retry_genome, retry_result

    return best_genome, best_result


__all__ = ["LocalLnsConfig", "run_local_lns"]
