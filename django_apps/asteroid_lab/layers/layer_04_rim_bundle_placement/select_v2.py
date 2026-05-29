"""L4 v2 component-local packing selection."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeStatus,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    Layer04PackingObservability,
    RimComponentSelectionRecord,
    RimPackingRejectionKind,
    RimPlacementRejection,
    RimPlacementRejectReason,
    RimSelectionStrategy,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.conflict_graph import (
    build_conflict_components,
    occupied_cells_for_entry,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.exact_pack import (
    MAX_EXACT_COMPONENT_SIZE,
    select_max_set_score_independent_set,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select import (
    select_non_overlapping_candidates,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    candidate_sort_key,
    effective_mining_gain,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

OBSERVABILITY_BASELINE_BUDGET_MS = 60_000
_LOGICAL_GREEDY_BUDGET_MS = 60_000


@dataclass(frozen=True, slots=True)
class Layer04SelectionOutcome:
    selected_entries: tuple[RouteProbedBundleCandidate, ...]
    rejected: tuple[RimPlacementRejection, ...]
    packing_observability: Layer04PackingObservability


def compute_greedy_baseline_observability(
    *,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    observability_budget_ms: int = OBSERVABILITY_BASELINE_BUDGET_MS,
) -> tuple[int | None, str | None]:
    """Run v1 greedy on a cloned budget; never touches runtime selection budget."""

    baseline_ctx = LayerBudgetContext.from_budget_ms(observability_budget_ms)
    selected, _rejected = select_non_overlapping_candidates(
        normal_candidates=normal_candidates,
        budget_ctx=baseline_ctx,
    )
    total = sum(effective_mining_gain(e.candidate) for e in selected)
    return total, None


def select_non_overlapping_candidates_v2(
    *,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    budget_ctx: LayerBudgetContext,
) -> Layer04SelectionOutcome:
    succeeded = tuple(
        e for e in normal_candidates if e.route_probe_status is RouteProbeStatus.SUCCEEDED
    )
    failed = tuple(
        e for e in normal_candidates if e.route_probe_status is not RouteProbeStatus.SUCCEEDED
    )

    rejected: list[RimPlacementRejection] = []
    for entry in failed:
        rejected.append(_non_succeeded_rejection(entry))

    components = build_conflict_components(succeeded)
    component_records: list[RimComponentSelectionRecord] = []
    logical_by_component: dict[str, tuple[RouteProbedBundleCandidate, ...]] = {}

    greedy_logical_ctx = LayerBudgetContext.from_budget_ms(_LOGICAL_GREEDY_BUDGET_MS)

    for component in components:
        strategy = (
            RimSelectionStrategy.EXACT_PACK
            if component.node_count <= MAX_EXACT_COMPONENT_SIZE
            else RimSelectionStrategy.GREEDY_FALLBACK
        )
        if strategy is RimSelectionStrategy.EXACT_PACK:
            logical = select_max_set_score_independent_set(component.entries)
        else:
            logical, _rej = select_non_overlapping_candidates(
                normal_candidates=component.entries,
                budget_ctx=greedy_logical_ctx,
            )
        logical_by_component[component.component_id] = logical
        component_records.append(
            RimComponentSelectionRecord(
                component_id=component.component_id,
                component_sort_key=component.component_sort_key,
                node_count=component.node_count,
                selection_strategy=strategy,
                selected_candidate_ids=tuple(e.candidate.candidate_id for e in logical),
                materialized_candidate_ids=(),
                total_effective_mining_gain=sum(
                    effective_mining_gain(e.candidate) for e in logical
                ),
                selected_count=len(logical),
            )
        )

    materialization_queue: list[tuple[str, RouteProbedBundleCandidate]] = []
    for component in components:
        logical = logical_by_component[component.component_id]
        for entry in sorted(logical, key=candidate_sort_key):
            materialization_queue.append((component.component_id, entry))

    selected_entries: list[RouteProbedBundleCandidate] = []
    materialized_by_component: dict[str, list[str]] = {c.component_id: [] for c in components}
    budget_limited = False
    budget_interrupted_component_id: str | None = None

    for component_id, entry in materialization_queue:
        if budget_ctx.remaining_budget_ms() <= 0:
            budget_limited = True
            if budget_interrupted_component_id is None:
                budget_interrupted_component_id = component_id
            rejected.append(_budget_rejection(entry, component_id))
            continue
        selected_entries.append(entry)
        materialized_by_component[component_id].append(entry.candidate.candidate_id)

    materialized_ids = {e.candidate.candidate_id for e in selected_entries}

    for component in components:
        component_id = component.component_id
        logical = logical_by_component[component_id]
        winner_ids = {e.candidate.candidate_id for e in logical}
        winner_ref = _winner_reference(logical, materialized_by_component[component_id])

        for entry in component.entries:
            cid = entry.candidate.candidate_id
            if cid in materialized_ids:
                continue
            if cid not in winner_ids:
                rejected.append(
                    _packing_set_loser_rejection(
                        entry=entry,
                        component_id=component_id,
                        winner=winner_ref,
                    )
                )

    updated_records = tuple(
        RimComponentSelectionRecord(
            component_id=rec.component_id,
            component_sort_key=rec.component_sort_key,
            node_count=rec.node_count,
            selection_strategy=rec.selection_strategy,
            selected_candidate_ids=rec.selected_candidate_ids,
            materialized_candidate_ids=tuple(materialized_by_component[rec.component_id]),
            total_effective_mining_gain=rec.total_effective_mining_gain,
            selected_count=rec.selected_count,
        )
        for rec in component_records
    )

    selected_total_gain = sum(effective_mining_gain(e.candidate) for e in selected_entries)
    baseline_gain, baseline_skip = compute_greedy_baseline_observability(
        normal_candidates=normal_candidates,
    )

    observability = Layer04PackingObservability(
        greedy_baseline_total_gain=baseline_gain,
        selected_total_gain=selected_total_gain,
        greedy_baseline_skipped_reason=baseline_skip,
        budget_limited=budget_limited,
        budget_interrupted_component_id=budget_interrupted_component_id,
        component_records=updated_records,
    )

    return Layer04SelectionOutcome(
        selected_entries=tuple(selected_entries),
        rejected=tuple(rejected),
        packing_observability=observability,
    )


def _winner_reference(
    logical: tuple[RouteProbedBundleCandidate, ...],
    materialized_ids: list[str],
) -> RouteProbedBundleCandidate | None:
    if materialized_ids:
        first_id = materialized_ids[0]
        for entry in logical:
            if entry.candidate.candidate_id == first_id:
                return entry
    if logical:
        return logical[0]
    return None


def _packing_set_loser_rejection(
    *,
    entry: RouteProbedBundleCandidate,
    component_id: str,
    winner: RouteProbedBundleCandidate | None,
) -> RimPlacementRejection:
    loser = entry.candidate
    conflict_cells: frozenset[Coord] = frozenset()
    winner_id: str | None = None
    winner_gain: int | None = None
    winner_dir: str | None = None
    if winner is not None:
        conflict_cells = frozenset(
            occupied_cells_for_entry(entry) & occupied_cells_for_entry(winner)
        )
        winner_id = winner.candidate.candidate_id
        winner_gain = effective_mining_gain(winner.candidate)
        winner_dir = winner.candidate.output_dir.value
    return RimPlacementRejection(
        candidate_id=loser.candidate_id,
        equivalence_key=loser.equivalence_key,
        reason=RimPlacementRejectReason.PHYSICAL_OVERLAP,
        conflicting_candidate_id=winner_id,
        conflicting_cells=conflict_cells,
        rejected_candidate_id=loser.candidate_id,
        rejected_output_dir=loser.output_dir.value,
        rejected_mining_cell_count=effective_mining_gain(loser),
        conflicting_winner_candidate_id=winner_id,
        conflicting_winner_output_dir=winner_dir,
        conflicting_winner_mining_cell_count=winner_gain,
        winner_selected_due_to_higher_mining_gain=False,
        packing_component_id=component_id,
        packing_rejection_kind=RimPackingRejectionKind.PACKING_SET_LOSER,
        winner_selected_due_to_higher_set_score=True,
    )


def _budget_rejection(
    entry: RouteProbedBundleCandidate,
    component_id: str,
) -> RimPlacementRejection:
    loser = entry.candidate
    return RimPlacementRejection(
        candidate_id=loser.candidate_id,
        equivalence_key=loser.equivalence_key,
        reason=RimPlacementRejectReason.BUDGET_INTERRUPTED,
        rejected_candidate_id=loser.candidate_id,
        rejected_output_dir=loser.output_dir.value,
        rejected_mining_cell_count=effective_mining_gain(loser),
        packing_component_id=component_id,
        packing_rejection_kind=RimPackingRejectionKind.BUDGET_INTERRUPTED,
    )


def _non_succeeded_rejection(entry: RouteProbedBundleCandidate) -> RimPlacementRejection:
    loser = entry.candidate
    return RimPlacementRejection(
        candidate_id=loser.candidate_id,
        equivalence_key=loser.equivalence_key,
        reason=RimPlacementRejectReason.NON_SUCCEEDED_PROBE,
        rejected_candidate_id=loser.candidate_id,
        rejected_output_dir=loser.output_dir.value,
        rejected_mining_cell_count=effective_mining_gain(loser),
        packing_rejection_kind=RimPackingRejectionKind.NON_SUCCEEDED_PROBE,
    )


__all__ = [
    "OBSERVABILITY_BASELINE_BUDGET_MS",
    "Layer04SelectionOutcome",
    "compute_greedy_baseline_observability",
    "select_non_overlapping_candidates_v2",
]
