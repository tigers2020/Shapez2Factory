"""Pattern-intrinsic difficulty scoring for miner seed catalog rows."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.genetic_sample.miner_seed_parent_tree import (
    EquipmentNodes,
    equipment_nodes,
    parent_edges_bfs,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.snapshots.island_bbox import island_bbox_from_xy_dicts

_LINEAR_CHAIN_BONUS = 15
_THROUGHPUT_SOFT_CAP = 12

LOW_EXTENSION_FALLBACK_PENALTY_BY_EXT: dict[int, int] = {
    3: 0,
    2: 40,
    1: 220,
    0: 400,
}

ParentEdge = tuple[tuple[int, int], tuple[int, int]]
SortKey = tuple[int, int, float, int, str]


@dataclass(frozen=True)
class IntrinsicDifficultyResult:
    score: int
    tier: int
    reason: dict[str, object]


def _branch_count(edges: list[ParentEdge]) -> int:
    children: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for child, parent in edges:
        children.setdefault(parent, []).append(child)
    return sum(1 for parent, ch in children.items() if len(ch) > 1)


def _turn_count(
    miner_xy: tuple[int, int],
    nodes: EquipmentNodes,
    edges: list[ParentEdge],
) -> int:
    parent_map = {child: parent for child, parent in edges}
    children: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for child, parent in edges:
        children.setdefault(parent, []).append(child)
    leaves = [xy for xy in nodes if xy != miner_xy and xy not in children]
    total_turns = 0
    for leaf in leaves:
        path: list[tuple[int, int]] = []
        cur: tuple[int, int] | None = leaf
        while cur is not None and cur != miner_xy:
            path.append(cur)
            cur = parent_map.get(cur)
        path.append(miner_xy)
        path.reverse()
        for i in range(1, len(path) - 1):
            a, b, c = path[i - 1], path[i], path[i + 1]
            da = (b[0] - a[0], b[1] - a[1])
            db = (c[0] - b[0], c[1] - b[1])
            if da != db:
                total_turns += 1
    return total_turns


def _difficulty_tier(extension_count: int, branch_count: int, turn_count: int) -> int:
    if extension_count == 0:
        return 0
    if extension_count == 1:
        return 1
    if extension_count == 2:
        return 2 if branch_count == 0 else 3
    if extension_count == 3:
        if branch_count == 0 and turn_count <= 1:
            return 4
        return 5
    return 5


def intrinsic_difficulty_from_root(root: dict[str, object]) -> IntrinsicDifficultyResult:
    miner_xy, nodes = equipment_nodes(root)
    edges = parent_edges_bfs(miner_xy, nodes)
    extension_count = count_extensions(root)
    throughput_factor = throughput_factor_for_extension_count(extension_count)
    occupied_cell_count = len(nodes)
    bbox = island_bbox_from_xy_dicts([{"x": xy[0], "y": xy[1]} for xy in nodes]) or {}
    bbox_width = int(bbox.get("width", 1))
    bbox_height = int(bbox.get("height", 1))
    bbox_area = bbox_width * bbox_height
    max_span = max(bbox_width, bbox_height)
    branches = _branch_count(edges)
    turns = _turn_count(miner_xy, nodes, edges)
    linear_chain = extension_count > 0 and branches == 0
    linear_chain_bonus = _LINEAR_CHAIN_BONUS if linear_chain else 0
    throughput_soft_penalty = min(throughput_factor * 2, _THROUGHPUT_SOFT_CAP)
    compactness_approx = occupied_cell_count / bbox_area if bbox_area else 0.0
    score = (
        extension_count * 100
        + occupied_cell_count * 8
        + bbox_area * 5
        + max_span * 3
        + branches * 25
        + turns * 10
        - linear_chain_bonus
        - throughput_soft_penalty
    )
    tier = _difficulty_tier(extension_count, branches, turns)
    reason: dict[str, object] = {
        "extension_count": extension_count,
        "occupied_cell_count": occupied_cell_count,
        "bbox_width": bbox_width,
        "bbox_height": bbox_height,
        "bbox_area": bbox_area,
        "max_span": max_span,
        "branch_count": branches,
        "turn_count": turns,
        "linear_chain_bonus": linear_chain_bonus,
        "throughput_factor": throughput_factor,
        "throughput_soft_penalty": throughput_soft_penalty,
        "compactness_approx": compactness_approx,
    }
    return IntrinsicDifficultyResult(score=score, tier=tier, reason=reason)


def pre_pattern_id_sort_key(result: IntrinsicDifficultyResult) -> tuple[int, int, float, int]:
    """Sort key before final ``pattern_id`` tie-break (for strict ambiguity checks)."""

    return (
        result.tier,
        result.score,
        float(result.reason["compactness_approx"]),
        int(result.reason["throughput_factor"]),
    )


def find_rank_ambiguity(
    items: list[tuple[str, IntrinsicDifficultyResult]],
) -> list[tuple[str, str, tuple[int, int, float, int]]]:
    """Return (pattern_id_a, pattern_id_b, shared_key) for colliding pre-pattern_id keys."""

    by_key: dict[tuple[int, int, float, int], str] = {}
    collisions: list[tuple[str, str, tuple[int, int, float, int]]] = []
    for pattern_id, result in items:
        key = pre_pattern_id_sort_key(result)
        prior = by_key.get(key)
        if prior is not None and prior != pattern_id:
            collisions.append((prior, pattern_id, key))
        else:
            by_key[key] = pattern_id
    return collisions


def intrinsic_priority_score(result: IntrinsicDifficultyResult) -> int:
    """Production-adjusted intrinsic priority (lower = try first in gene picker)."""

    ext = int(result.reason["extension_count"])
    throughput = int(result.reason["throughput_factor"])
    base = round((result.score * 10) / throughput)
    return base + LOW_EXTENSION_FALLBACK_PENALTY_BY_EXT[ext]


def assign_intrinsic_priority_ranks(
    items: list[tuple[str, IntrinsicDifficultyResult]],
) -> list[tuple[str, IntrinsicDifficultyResult, int]]:
    """Return (pattern_id, result, intrinsic_priority_rank) sorted highest-priority-first."""

    def sort_key(item: tuple[str, IntrinsicDifficultyResult]) -> tuple[int, int, int, str]:
        pattern_id, result = item
        return (
            intrinsic_priority_score(result),
            result.tier,
            result.score,
            pattern_id,
        )

    ordered = sorted(items, key=sort_key)
    return [
        (pattern_id, result, rank) for rank, (pattern_id, result) in enumerate(ordered, start=1)
    ]


def assign_difficulty_ranks(
    items: list[tuple[str, IntrinsicDifficultyResult]],
) -> list[tuple[str, IntrinsicDifficultyResult, int]]:
    """Return (pattern_id, result, difficulty_rank) sorted easiest-first; ranks 1..N."""

    def sort_key(item: tuple[str, IntrinsicDifficultyResult]) -> SortKey:
        pattern_id, result = item
        compactness = float(result.reason["compactness_approx"])
        throughput = int(result.reason["throughput_factor"])
        return (
            result.tier,
            result.score,
            -compactness,
            throughput,
            pattern_id,
        )

    ordered = sorted(items, key=sort_key)
    return [
        (pattern_id, result, rank) for rank, (pattern_id, result) in enumerate(ordered, start=1)
    ]


__all__ = [
    "IntrinsicDifficultyResult",
    "LOW_EXTENSION_FALLBACK_PENALTY_BY_EXT",
    "assign_difficulty_ranks",
    "assign_intrinsic_priority_ranks",
    "find_rank_ambiguity",
    "intrinsic_difficulty_from_root",
    "intrinsic_priority_score",
    "pre_pattern_id_sort_key",
]
