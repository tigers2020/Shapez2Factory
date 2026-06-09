"""Artifact-level golden oracle evaluation (no blueprint assembler required)."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
    GoldenOracle,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverArtifacts,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_l4_capacity_metrics import (
    compute_golden_l4_capacity_metrics,
    format_l4_capacity_diagnostics,
)
from shapez2_factory.application.asteroid_lab.experiments.transport_kind_normalization import (
    format_transport_kind_mismatch_diagnostic,
    transport_families_compatible,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_failed_source_diagnostics import (  # noqa: E501
    format_l5_failure_eval_diagnostics,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    resolve_canonical_layer_slug,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_throughput import (  # noqa: E501
    mini_unit_output_per_min_for_resource,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

_REQUIRED_STACK_LAYERS = (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)


@dataclass(frozen=True, slots=True)
class GoldenEvalResult:
    valid: bool
    score: float
    miner_count: int
    belt_count: int
    routed_throughput: float
    anchor_f1_direct: float
    anchor_f1_normalized: float
    golden_belt_similarity: float
    route_island_count: int
    orphan_count: int
    diagnostics: tuple[str, ...]


def _f1_score(expected: frozenset[tuple[int, int]], actual: frozenset[tuple[int, int]]) -> float:
    if not expected and not actual:
        return 1.0
    if not expected or not actual:
        return 0.0
    tp = len(expected & actual)
    if tp == 0:
        return 0.0
    precision = tp / len(actual)
    recall = tp / len(expected)
    return 2 * precision * recall / (precision + recall)


def _candidate_extractor_anchors_direct(
    artifacts: GoldenSolverArtifacts,
) -> frozenset[tuple[int, int]]:
    rim = artifacts.rim_result
    if rim is None:
        return frozenset()
    return frozenset(
        (placement.anchor[0], placement.anchor[1]) for placement in rim.committed_placements
    )


def _normalize_anchor_set(
    anchors: frozenset[tuple[int, int]],
) -> frozenset[tuple[int, int]]:
    if not anchors:
        return frozenset()
    ox, oy = min(anchors)
    return frozenset((x - ox, y - oy) for x, y in anchors)


def _belt_edges_from_paths(
    paths: frozenset[tuple[int, int]],
) -> frozenset[tuple[tuple[int, int], tuple[int, int]]]:
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for x, y in paths:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in paths:
                a, b = (x, y), (nx, ny)
                edge: tuple[tuple[int, int], tuple[int, int]] = (a, b) if a <= b else (b, a)
                edges.add(edge)
    return frozenset(edges)


def _jaccard(a: frozenset[object], b: frozenset[object]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def _connectivity_roots(artifacts: GoldenSolverArtifacts) -> frozenset[Coord]:
    """BFS roots from L2 connectors and L5 route group cells only."""

    roots: set[Coord] = set()
    plan = artifacts.exterior_plan
    if plan is not None:
        for connector in plan.planned_connectors:
            roots.add(connector.void_coord)
            roots.update(connector.coords)
    route_plan = artifacts.route_plan
    if route_plan is not None:
        for group in route_plan.groups:
            roots.update(group.route_cells)
    return frozenset(roots)


def _route_cells_from_plan(artifacts: GoldenSolverArtifacts) -> frozenset[Coord]:
    route_plan = artifacts.route_plan
    if route_plan is None:
        return frozenset()
    cells: set[Coord] = set()
    for route in route_plan.routes:
        cells.update(route.path_coords)
    return frozenset(cells)


def _route_island_count(
    route_cells: frozenset[Coord],
    roots: frozenset[Coord],
) -> int:
    if not route_cells:
        return 0
    reachable: set[Coord] = set()
    frontier = [c for c in roots if c in route_cells]
    if not frontier:
        frontier = [c for c in roots]
    for start in frontier:
        if start in reachable:
            continue
        stack = [start]
        while stack:
            cell = stack.pop()
            if cell in reachable or cell not in route_cells:
                continue
            reachable.add(cell)
            x, y = cell
            for nbr in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nbr in route_cells and nbr not in reachable:
                    stack.append(nbr)
    islands = 0
    visited: set[Coord] = set()
    for cell in route_cells:
        if cell in visited:
            continue
        if cell in reachable:
            visited.add(cell)
            continue
        islands += 1
        stack = [cell]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            x, y = cur
            for nbr in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nbr in route_cells and nbr not in visited:
                    stack.append(nbr)
    return islands


def _orphan_count(route_cells: frozenset[Coord]) -> int:
    if not route_cells:
        return 0
    dead_ends = 0
    for x, y in route_cells:
        neighbors = sum(
            1
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
            if (nx, ny) in route_cells
        )
        if neighbors == 0:
            dead_ends += 1
    return dead_ends


def _l3_footprints_overlap(artifacts: GoldenSolverArtifacts) -> bool:
    rim = artifacts.rim_result
    if rim is None:
        return False
    occupied: set[Coord] = set()
    for placement in rim.committed_placements:
        footprint = placement.miner_cells | placement.extension_cells
        if occupied & footprint:
            return True
        occupied |= footprint
    return False


def _stack_l2_l5_complete(
    artifacts: GoldenSolverArtifacts,
    diagnostics: list[str],
) -> bool:
    completed = {
        resolve_canonical_layer_slug(slug)
        for slug in artifacts.core_result.stack_result.completed_layer_slugs
    }
    summary_by_slug = {
        resolve_canonical_layer_slug(record.layer_slug): record
        for record in artifacts.layer_summaries
    }
    for slug in _REQUIRED_STACK_LAYERS:
        if slug not in completed:
            diagnostics.append(f"missing_layer:{slug}")
            return False
        record = summary_by_slug.get(slug)
        if record is None or record.outcome != LayerPostSummaryOutcome.COMPLETED:
            diagnostics.append(f"layer_not_completed:{slug}")
            return False
    return True


def _routed_throughput_per_min(artifacts: GoldenSolverArtifacts) -> float:
    """L5-confirmed throughput: only placements with committed routes count."""

    route_plan = artifacts.route_plan
    rim = artifacts.rim_result
    if route_plan is None or rim is None:
        return 0.0
    routed_ids = {route.placement_id for route in route_plan.routes}
    resource_kind = route_plan.resource_kind
    unit_rate = mini_unit_output_per_min_for_resource(resource_kind)
    total = 0.0
    for placement in rim.committed_placements:
        if placement.placement_id not in routed_ids:
            continue
        total += float(int(unit_rate) * placement.throughput_factor)
    return total


def _hard_validity(
    artifacts: GoldenSolverArtifacts,
    diagnostics: list[str],
) -> bool:
    if not _stack_l2_l5_complete(artifacts, diagnostics):
        return False
    stack = artifacts.core_result.stack_result
    if stack.failed_layer_slug is not None:
        diagnostics.append(f"stack_failed_layer:{stack.failed_layer_slug}")
        return False
    if artifacts.exterior_plan is None:
        diagnostics.append("missing_exterior_plan")
        return False
    if _l3_footprints_overlap(artifacts):
        diagnostics.append("l3_footprint_overlap")
        return False
    route_plan = artifacts.route_plan
    if route_plan is None:
        diagnostics.append("missing_route_plan")
        return False
    metrics = route_plan.metrics
    if metrics.failed_source_count != 0:
        diagnostics.append(f"l5_failed_sources:{metrics.failed_source_count}")
        return False
    if metrics.source_count > 0 and metrics.routed_source_count != metrics.source_count:
        diagnostics.append(
            f"l5_routed_mismatch:{metrics.routed_source_count}/{metrics.source_count}",
        )
        return False
    exterior = artifacts.exterior_plan
    if not transport_families_compatible(
        exterior_transport_kind=exterior.transport_kind,
        route_transport_kind=route_plan.transport_kind,
    ):
        diagnostics.append(
            format_transport_kind_mismatch_diagnostic(
                exterior_transport_kind=exterior.transport_kind,
                route_transport_kind=route_plan.transport_kind,
            )
        )
        return False
    return True


def evaluate_against_golden(
    artifacts: GoldenSolverArtifacts,
    golden_oracle: GoldenOracle,
) -> GoldenEvalResult:
    diagnostics: list[str] = []
    valid = _hard_validity(artifacts, diagnostics)

    rim = artifacts.rim_result
    route_plan = artifacts.route_plan
    miner_count = len(rim.committed_placements) if rim is not None else 0
    belt_count = route_plan.metrics.total_route_cells if route_plan is not None else 0
    routed_throughput = _routed_throughput_per_min(artifacts)

    candidate_direct = _candidate_extractor_anchors_direct(artifacts)
    candidate_normalized = _normalize_anchor_set(candidate_direct)
    anchor_f1_direct = _f1_score(golden_oracle.extractor_anchors_direct, candidate_direct)
    anchor_f1_normalized = _f1_score(
        golden_oracle.extractor_anchors_normalized,
        candidate_normalized,
    )

    route_cells = _route_cells_from_plan(artifacts)
    candidate_belt_edges = _belt_edges_from_paths(route_cells)
    golden_belt_similarity = _jaccard(candidate_belt_edges, golden_oracle.belt_edges)

    roots = _connectivity_roots(artifacts)
    route_island_count = _route_island_count(route_cells, roots)
    orphan_count = _orphan_count(route_cells)

    routed_sources = route_plan.metrics.routed_source_count if route_plan else 0
    congestion_penalty = belt_count / (routed_sources + 1) if route_plan else 0.0

    score = 0.0
    if valid:
        score = (
            1_000_000
            + 10_000 * routed_throughput
            + 1_000 * miner_count
            + 300 * anchor_f1_direct
            + 200 * golden_belt_similarity
            - 20 * belt_count
            - 50 * orphan_count
            - 100 * route_island_count
            - 10 * congestion_penalty
        )

    if anchor_f1_normalized < anchor_f1_direct:
        diagnostics.append("anchor_normalized_below_direct")

    diagnostics.extend(format_l5_failure_eval_diagnostics(route_plan))
    diagnostics.extend(
        format_l4_capacity_diagnostics(compute_golden_l4_capacity_metrics(artifacts)),
    )

    return GoldenEvalResult(
        valid=valid,
        score=score,
        miner_count=miner_count,
        belt_count=belt_count,
        routed_throughput=routed_throughput,
        anchor_f1_direct=anchor_f1_direct,
        anchor_f1_normalized=anchor_f1_normalized,
        golden_belt_similarity=golden_belt_similarity,
        route_island_count=route_island_count,
        orphan_count=orphan_count,
        diagnostics=tuple(diagnostics),
    )


__all__ = ["GoldenEvalResult", "evaluate_against_golden"]
