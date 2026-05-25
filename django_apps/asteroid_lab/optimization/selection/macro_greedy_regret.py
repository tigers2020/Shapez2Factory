"""Greedy-regret macro genome selection for RTTP v1 (PR-D, RTTP-G12)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.macros.macro_dtos import MacroBundleCandidate
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
    _inlet_fragility,
    _rim_port_alignment,
)
from django_apps.asteroid_lab.optimization.selection.macro_equivalence import (
    MacroEquivalenceKey,
    dedupe_macros,
    macro_equivalence_key,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4


def assert_macro_only_commit_order(
    genome: PlacementGenome,
    macro_normal: tuple[MacroBundleCandidate, ...],
    *,
    pipeline_config: RttpPipelineConfig,
) -> None:
    """Reject singleton ``candidate_id`` slots when ``allow_singleton_genome_slots`` is false."""

    if pipeline_config.allow_singleton_genome_slots:
        return
    macro_ids = {row.macro_id for row in macro_normal}
    child_ids = {child.candidate_id for row in macro_normal for child in row.macro.children}
    for slot_id in genome.commit_order:
        if slot_id in child_ids and slot_id not in macro_ids:
            msg = f"singleton child id in genome commit_order: {slot_id!r}"
            raise ValueError(msg)
        if slot_id not in macro_ids:
            msg = f"commit_order slot is not a macro_id: {slot_id!r}"
            raise ValueError(msg)


def _macro_rim_alignment(macro_row: MacroBundleCandidate, skeleton: RttpSkeleton) -> float:
    return sum(_rim_port_alignment(child, skeleton) for child in macro_row.macro.children)


def _macro_inlet_fragility(
    macro_row: MacroBundleCandidate,
    skeleton: RttpSkeleton,
    committed_route_cells: frozenset[Coord],
) -> float:
    return sum(
        _inlet_fragility(child, skeleton, committed_route_cells)
        for child in macro_row.macro.children
    )


def _macro_fragmentation(
    macro_row: MacroBundleCandidate,
    inp: OptimizationInput,
    committed_occupied: frozenset[Coord],
) -> float:
    remaining = inp.mineable_cells - committed_occupied - macro_row.macro.combined_occupied_cells
    if not remaining:
        return 0.0
    isolated = 0
    for cell in remaining:
        if not any(neighbor in remaining for neighbor in neighbors4(cell)):
            isolated += 1
    return float(isolated) / float(len(remaining))


def _base_macro_score(
    macro_row: MacroBundleCandidate,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig,
    committed_occupied: frozenset[Coord],
) -> float:
    probe_cost = sum(child.route_probe_cost for child in macro_row.macro.children)
    return (
        1000.0 * float(macro_row.macro.macro_throughput_factor)
        + config.rim_port_alignment_weight * _macro_rim_alignment(macro_row, skeleton)
        - 30.0 * float(probe_cost)
        - config.fragmentation_weight * _macro_fragmentation(macro_row, inp, committed_occupied)
    )


def _macro_regret_scores(
    pool: tuple[MacroBundleCandidate, ...],
    base_scores: dict[str, float],
) -> dict[str, float]:
    by_key: dict[MacroEquivalenceKey, list[MacroBundleCandidate]] = {}
    for row in pool:
        by_key.setdefault(macro_equivalence_key(row.macro), []).append(row)

    regrets: dict[str, float] = {}
    for group in by_key.values():
        ordered = sorted(
            group,
            key=lambda item: base_scores[item.macro_id],
            reverse=True,
        )
        if len(ordered) == 1:
            regrets[ordered[0].macro_id] = 0.0
            continue
        second_best = base_scores[ordered[1].macro_id]
        for row in ordered:
            regrets[row.macro_id] = base_scores[row.macro_id] - second_best
    return regrets


def _macro_priority(
    macro_row: MacroBundleCandidate,
    *,
    base_score: float,
    regret: float,
    skeleton: RttpSkeleton,
    committed_route_cells: frozenset[Coord],
    config: SelectionConfig,
) -> float:
    inlet = _macro_inlet_fragility(macro_row, skeleton, committed_route_cells)
    return base_score + config.lambda_regret * regret - config.inlet_fragility_weight * inlet


def _macro_overlaps(macro_row: MacroBundleCandidate, occupied: frozenset[Coord]) -> bool:
    return bool(macro_row.macro.combined_occupied_cells & occupied)


def select_macro_genome(
    macro_normal: tuple[MacroBundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    pipeline_config: RttpPipelineConfig | None = None,
    selection_config: SelectionConfig | None = None,
    goal_count: int | None = None,
) -> PlacementGenome:
    """Greedy-regret on macro pool; ``commit_order`` lists ``macro_id`` only."""

    resolved_pipeline = pipeline_config or RttpPipelineConfig()
    resolved_selection = selection_config or SelectionConfig()
    pool = list(dedupe_macros(macro_normal))
    commit_order: list[str] = []
    committed_occupied: set[Coord] = set()
    committed_route_cells: set[Coord] = set()
    resolved_goal = (
        max(0, goal_count) if goal_count is not None else max(0, skeleton.capacity_goals)
    )

    while pool and len(commit_order) < resolved_goal:
        base_scores = {
            row.macro_id: _base_macro_score(
                row,
                skeleton,
                inp,
                config=resolved_selection,
                committed_occupied=frozenset(committed_occupied),
            )
            for row in pool
        }
        regrets = _macro_regret_scores(tuple(pool), base_scores)

        best = max(
            pool,
            key=lambda row: (
                _macro_priority(
                    row,
                    base_score=base_scores[row.macro_id],
                    regret=regrets[row.macro_id],
                    skeleton=skeleton,
                    committed_route_cells=frozenset(committed_route_cells),
                    config=resolved_selection,
                ),
                -pool.index(row),
            ),
        )
        commit_order.append(best.macro_id)
        committed_occupied.update(best.macro.combined_occupied_cells)
        for child in best.macro.children:
            committed_route_cells.add(child.output_stub)
        pool = [
            row
            for row in pool
            if row.macro_id != best.macro_id
            and not _macro_overlaps(row, frozenset(committed_occupied))
        ]

    genome = PlacementGenome(commit_order=tuple(commit_order))
    assert_macro_only_commit_order(
        genome,
        macro_normal,
        pipeline_config=resolved_pipeline,
    )
    return genome


__all__ = [
    "assert_macro_only_commit_order",
    "select_macro_genome",
]
