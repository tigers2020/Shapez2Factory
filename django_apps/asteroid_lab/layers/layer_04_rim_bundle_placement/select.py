"""Deterministic physical non-overlap selection for Layer 04."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeStatus,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    RimPlacementRejection,
    RimPlacementRejectReason,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    candidate_sort_key,
    effective_mining_gain,
    overlap_tiebreak_step,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def _occupied_cells(entry: RouteProbedBundleCandidate) -> frozenset[Coord]:
    c = entry.candidate
    return c.mining_occupied_cells | c.transport_stub_cells


def _find_conflicting_selected(
    cells: frozenset[Coord],
    selected: tuple[RouteProbedBundleCandidate, ...],
) -> RouteProbedBundleCandidate | None:
    for prior in selected:
        if _occupied_cells(prior) & cells:
            return prior
    return None


def _physical_overlap_rejection(
    *,
    entry: RouteProbedBundleCandidate,
    winner: RouteProbedBundleCandidate,
    conflict_cells: frozenset[Coord],
) -> RimPlacementRejection:
    loser = entry.candidate
    win = winner.candidate
    loser_gain = effective_mining_gain(loser)
    winner_gain = effective_mining_gain(win)
    higher = winner_gain > loser_gain
    return RimPlacementRejection(
        candidate_id=loser.candidate_id,
        equivalence_key=loser.equivalence_key,
        reason=RimPlacementRejectReason.PHYSICAL_OVERLAP,
        conflicting_candidate_id=win.candidate_id,
        conflicting_cells=conflict_cells,
        rejected_candidate_id=loser.candidate_id,
        rejected_output_dir=loser.output_dir.value,
        rejected_mining_cell_count=loser_gain,
        conflicting_winner_candidate_id=win.candidate_id,
        conflicting_winner_output_dir=win.output_dir.value,
        conflicting_winner_mining_cell_count=winner_gain,
        winner_selected_due_to_higher_mining_gain=higher,
        overlap_tiebreak_step=None if higher else overlap_tiebreak_step(winner, entry),
    )


def select_non_overlapping_candidates(
    *,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    budget_ctx: LayerBudgetContext,
) -> tuple[tuple[RouteProbedBundleCandidate, ...], tuple[RimPlacementRejection, ...]]:
    succeeded = tuple(
        e for e in normal_candidates if e.route_probe_status is RouteProbeStatus.SUCCEEDED
    )
    failed = tuple(
        e for e in normal_candidates if e.route_probe_status is not RouteProbeStatus.SUCCEEDED
    )

    ordered = tuple(sorted(succeeded, key=candidate_sort_key))
    selected: list[RouteProbedBundleCandidate] = []
    rejected: list[RimPlacementRejection] = []

    for entry in failed:
        rejected.append(
            RimPlacementRejection(
                candidate_id=entry.candidate.candidate_id,
                equivalence_key=entry.candidate.equivalence_key,
                reason=RimPlacementRejectReason.NON_SUCCEEDED_PROBE,
                rejected_candidate_id=entry.candidate.candidate_id,
                rejected_output_dir=entry.candidate.output_dir.value,
                rejected_mining_cell_count=effective_mining_gain(entry.candidate),
            )
        )

    occupied: set[Coord] = set()

    for entry in ordered:
        if budget_ctx.remaining_budget_ms() <= 0:
            rejected.append(
                RimPlacementRejection(
                    candidate_id=entry.candidate.candidate_id,
                    equivalence_key=entry.candidate.equivalence_key,
                    reason=RimPlacementRejectReason.BUDGET_INTERRUPTED,
                    rejected_candidate_id=entry.candidate.candidate_id,
                    rejected_output_dir=entry.candidate.output_dir.value,
                    rejected_mining_cell_count=effective_mining_gain(entry.candidate),
                )
            )
            continue

        cells = _occupied_cells(entry)
        conflict_cells = frozenset(cells & occupied)
        if conflict_cells:
            winner = _find_conflicting_selected(cells, tuple(selected))
            if winner is None:
                rejected.append(
                    RimPlacementRejection(
                        candidate_id=entry.candidate.candidate_id,
                        equivalence_key=entry.candidate.equivalence_key,
                        reason=RimPlacementRejectReason.PHYSICAL_OVERLAP,
                        conflicting_cells=conflict_cells,
                        rejected_candidate_id=entry.candidate.candidate_id,
                        rejected_output_dir=entry.candidate.output_dir.value,
                        rejected_mining_cell_count=effective_mining_gain(entry.candidate),
                    )
                )
                continue
            rejected.append(
                _physical_overlap_rejection(
                    entry=entry,
                    winner=winner,
                    conflict_cells=conflict_cells,
                )
            )
            continue

        selected.append(entry)
        occupied |= set(cells)

    return tuple(selected), tuple(rejected)


__all__ = ["select_non_overlapping_candidates"]
