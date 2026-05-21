"""Commit-order diversity — interleave selected candidates before incremental commit (PR)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_score import goal_load_key_for_candidate
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan

ANCHOR_REGION_BUCKET_SIZE = 4


def path_corridor_signature(candidate: GeneCandidate) -> tuple[tuple[int, int], ...]:
    """Stable corridor key from generation-time probe path (commit reprobes separately)."""
    path = candidate.route_probe_result.path
    if path:
        return (path[0], path[-1], len(path))
    return (candidate.route_probe_start, candidate.fixed_output_transport)


def anchor_region_bucket(candidate: GeneCandidate) -> tuple[int, int]:
    ax, ay = candidate.extractor
    size = ANCHOR_REGION_BUCKET_SIZE
    return (ax // size, ay // size)


def diversity_bucket_key(candidate: GeneCandidate) -> tuple:
    """Group key for round-robin interleave (goal + corridor + anchor region)."""
    goal_coord, transport_kind = goal_load_key_for_candidate(candidate)
    goal_id = (goal_coord, transport_kind.value)
    return (goal_id, path_corridor_signature(candidate), anchor_region_bucket(candidate))


def _within_bucket_sort_key(
    candidate_id: str,
    candidates_by_id: Mapping[str, GeneCandidate],
) -> tuple[int, int, str]:
    candidate = candidates_by_id[candidate_id]
    return (
        -candidate.base_throughput,
        candidate.route_probe_result.cost,
        candidate_id,
    )


def diversify_commit_order(
    plan: SelectedCandidatePlan,
    candidates_by_id: Mapping[str, GeneCandidate],
) -> SelectedCandidatePlan:
    """Round-robin across goal/corridor/anchor buckets; avoid one corridor monopolizing commit."""

    buckets: dict[tuple, list[str]] = defaultdict(list)
    for candidate_id in plan.ordered_candidate_ids:
        candidate = candidates_by_id[candidate_id]
        buckets[diversity_bucket_key(candidate)].append(candidate_id)

    for bucket_key in buckets:
        buckets[bucket_key].sort(key=lambda cid: _within_bucket_sort_key(cid, candidates_by_id))

    bucket_keys = sorted(buckets.keys())
    queues = [buckets[key] for key in bucket_keys]
    interleaved: list[str] = []
    while any(queues):
        for queue in queues:
            if queue:
                interleaved.append(queue.pop(0))

    return SelectedCandidatePlan(ordered_candidate_ids=tuple(interleaved))
