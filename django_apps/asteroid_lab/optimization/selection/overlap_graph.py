"""Overlap conflict graph utilities for RTTP selection packing (P1-ELCP-RF-B1)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate

EXACT_MIS_MAX_COMPONENT_SIZE = 40


class UpperBoundMethod(StrEnum):
    COMPONENT_EXACT = "component_exact"
    GREEDY_COLORING = "greedy_coloring"
    MIXED = "mixed"
    TRIVIAL_VERTEX_COUNT = "trivial_vertex_count"


@dataclass(frozen=True, slots=True)
class OverlapPackingBounds:
    vertex_count: int
    edge_count: int
    connected_component_count: int
    greedy_regret_baseline: int
    best_known_independent_set_size: int
    exact_mis_size: int | None
    upper_bound: int
    upper_bound_method: UpperBoundMethod
    chromatic_upper_bound_sum: int
    component_sizes: tuple[int, ...]
    exact_mis_component_count: int
    heuristic_mis_component_count: int


def build_overlap_adjacency(
    candidates: Sequence[BundleCandidate],
) -> dict[str, frozenset[str]]:
    ids = [candidate.candidate_id for candidate in candidates]
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    adj: dict[str, set[str]] = {candidate_id: set() for candidate_id in ids}
    for left_index, left_id in enumerate(ids):
        left = by_id[left_id]
        for right_id in ids[left_index + 1 :]:
            right = by_id[right_id]
            if left.occupied_cells & right.occupied_cells:
                adj[left_id].add(right_id)
                adj[right_id].add(left_id)
    return {candidate_id: frozenset(neighbors) for candidate_id, neighbors in adj.items()}


def count_undirected_edges(adj: dict[str, frozenset[str]]) -> int:
    return sum(len(neighbors) for neighbors in adj.values()) // 2


def connected_components(adj: dict[str, frozenset[str]]) -> tuple[tuple[str, ...], ...]:
    remaining = set(adj)
    components: list[tuple[str, ...]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component: list[str] = []
        while stack:
            node = stack.pop()
            if node not in remaining:
                continue
            remaining.remove(node)
            component.append(node)
            for neighbor in sorted(adj[node]):
                if neighbor in remaining:
                    stack.append(neighbor)
        components.append(tuple(sorted(component)))
    components.sort(key=lambda item: (-len(item), item[0] if item else ""))
    return tuple(components)


def exact_mis_size_for_component(
    adj: dict[str, frozenset[str]],
    component: tuple[str, ...],
) -> int | None:
    if len(component) > EXACT_MIS_MAX_COMPONENT_SIZE:
        return None
    ordered = tuple(sorted(component))

    def recurse(nodes: tuple[str, ...]) -> int:
        if not nodes:
            return 0
        vertex = nodes[0]
        rest = nodes[1:]
        without_vertex = recurse(rest)
        independent_rest = tuple(
            neighbor for neighbor in rest if neighbor not in adj[vertex]
        )
        with_vertex = 1 + recurse(independent_rest)
        return max(without_vertex, with_vertex)

    return recurse(ordered)


def heuristic_mis_for_component(
    adj: dict[str, frozenset[str]],
    component: tuple[str, ...],
) -> int:
    remaining = set(component)
    independent_set_size = 0
    while remaining:
        pivot = min(
            remaining,
            key=lambda vertex: (len(adj[vertex] & remaining), vertex),
        )
        independent_set_size += 1
        remaining -= {pivot} | (adj[pivot] & remaining)
    return independent_set_size


def heuristic_mis_vertices_for_component(
    adj: dict[str, frozenset[str]],
    component: tuple[str, ...],
) -> tuple[str, ...]:
    remaining = set(component)
    picked: list[str] = []
    while remaining:
        pivot = min(
            remaining,
            key=lambda vertex: (len(adj[vertex] & remaining), vertex),
        )
        picked.append(pivot)
        remaining -= {pivot} | (adj[pivot] & remaining)
    return tuple(sorted(picked))


def greedy_coloring_upper_bound_for_component(
    adj: dict[str, frozenset[str]],
    component: tuple[str, ...],
) -> int:
    if not component:
        return 0
    ordered = sorted(
        component,
        key=lambda vertex: (-len(adj[vertex] & frozenset(component)), vertex),
    )
    color_by_vertex: dict[str, int] = {}
    for vertex in ordered:
        used = {
            color_by_vertex[neighbor]
            for neighbor in adj[vertex]
            if neighbor in color_by_vertex
        }
        color = 0
        while color in used:
            color += 1
        color_by_vertex[vertex] = color
    return max(color_by_vertex.values(), default=-1) + 1


def compute_target_floor(best_known_independent_set_size: int) -> int:
    if best_known_independent_set_size < 100:
        return best_known_independent_set_size
    return max(100, best_known_independent_set_size // 2)


def phase0_is_no_go(
    *,
    best_known_independent_set_size: int,
    greedy_regret_baseline: int,
    epsilon: int = 5,
) -> bool:
    return best_known_independent_set_size <= greedy_regret_baseline + epsilon


def compute_best_known_independent_set_candidate_ids(
    candidates: Sequence[BundleCandidate],
) -> tuple[str, ...]:
    adj = build_overlap_adjacency(candidates)
    picked: list[str] = []
    for component in connected_components(adj):
        exact = exact_mis_size_for_component(adj, component)
        if exact is not None:
            picked.extend(_exact_mis_vertices(adj, component))
        else:
            picked.extend(heuristic_mis_vertices_for_component(adj, component))
    return tuple(picked)


def _exact_mis_vertices(
    adj: dict[str, frozenset[str]],
    component: tuple[str, ...],
) -> tuple[str, ...]:
    ordered = tuple(sorted(component))

    def recurse(nodes: tuple[str, ...]) -> tuple[str, ...]:
        if not nodes:
            return ()
        vertex = nodes[0]
        rest = nodes[1:]
        without_vertex = recurse(rest)
        independent_rest = tuple(
            neighbor for neighbor in rest if neighbor not in adj[vertex]
        )
        with_vertex = (vertex,) + recurse(independent_rest)
        if len(with_vertex) > len(without_vertex):
            return with_vertex
        return without_vertex

    return recurse(ordered)


def compute_overlap_packing_bounds(
    candidates: Sequence[BundleCandidate],
    *,
    greedy_regret_baseline: int,
) -> OverlapPackingBounds:
    adj = build_overlap_adjacency(candidates)
    vertex_count = len(adj)
    components = connected_components(adj)
    best_known = 0
    upper_bound = 0
    chromatic_upper_bound_sum = 0
    exact_component_count = 0
    heuristic_component_count = 0
    component_sizes: list[int] = []
    all_exact = True
    any_exact = False
    any_heuristic = False

    for component in components:
        component_sizes.append(len(component))
        chromatic_upper_bound_sum += greedy_coloring_upper_bound_for_component(adj, component)
        exact_size = exact_mis_size_for_component(adj, component)
        if exact_size is not None:
            exact_component_count += 1
            any_exact = True
            best_known += exact_size
            upper_bound += exact_size
        else:
            all_exact = False
            heuristic_component_count += 1
            any_heuristic = True
            heuristic_size = heuristic_mis_for_component(adj, component)
            best_known += heuristic_size
            # |MIS| <= |V| per component; greedy coloring bounds χ, not |MIS|.
            upper_bound += len(component)

    if all_exact and vertex_count > 0:
        upper_bound_method = UpperBoundMethod.COMPONENT_EXACT
        exact_mis_size: int | None = best_known
    elif any_exact and any_heuristic:
        upper_bound_method = UpperBoundMethod.MIXED
        exact_mis_size = None
    else:
        upper_bound_method = UpperBoundMethod.GREEDY_COLORING
        exact_mis_size = best_known if vertex_count > 0 and not any_heuristic else None
        if vertex_count > 0 and not any_exact:
            exact_mis_size = None

    return OverlapPackingBounds(
        vertex_count=vertex_count,
        edge_count=count_undirected_edges(adj),
        connected_component_count=len(components),
        greedy_regret_baseline=greedy_regret_baseline,
        best_known_independent_set_size=best_known,
        exact_mis_size=exact_mis_size,
        upper_bound=upper_bound,
        upper_bound_method=upper_bound_method,
        chromatic_upper_bound_sum=chromatic_upper_bound_sum,
        component_sizes=tuple(component_sizes),
        exact_mis_component_count=exact_component_count,
        heuristic_mis_component_count=heuristic_component_count,
    )


__all__ = [
    "EXACT_MIS_MAX_COMPONENT_SIZE",
    "OverlapPackingBounds",
    "UpperBoundMethod",
    "build_overlap_adjacency",
    "compute_best_known_independent_set_candidate_ids",
    "compute_overlap_packing_bounds",
    "compute_target_floor",
    "connected_components",
    "count_undirected_edges",
    "exact_mis_size_for_component",
    "greedy_coloring_upper_bound_for_component",
    "heuristic_mis_for_component",
    "heuristic_mis_vertices_for_component",
    "phase0_is_no_go",
]
