"""Deterministic physical non-overlap selection for Layer 04."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    RimPlacementRejection,
    RimPlacementRejectReason,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def _candidate_sort_key(entry: RouteProbedBundleCandidate) -> tuple[int, int, int, str, str]:
    candidate = entry.candidate
    y, x = candidate.anchor_coord[1], candidate.anchor_coord[0]
    return (
        candidate.intrinsic_priority_rank,
        y,
        x,
        candidate.equivalence_key,
        candidate.candidate_id,
    )


def _occupied_cells(entry: RouteProbedBundleCandidate) -> frozenset[Coord]:
    c = entry.candidate
    return c.mining_occupied_cells | c.transport_stub_cells


def _find_conflicting_selected(
    cells: frozenset[Coord],
    selected: tuple[RouteProbedBundleCandidate, ...],
) -> str | None:
    for prior in selected:
        prior_cells = _occupied_cells(prior)
        if prior_cells & cells:
            return prior.candidate.candidate_id
    return None


def select_non_overlapping_candidates(
    *,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    budget_ctx: LayerBudgetContext,
) -> tuple[tuple[RouteProbedBundleCandidate, ...], tuple[RimPlacementRejection, ...]]:
    ordered = tuple(sorted(normal_candidates, key=_candidate_sort_key))
    selected: list[RouteProbedBundleCandidate] = []
    rejected: list[RimPlacementRejection] = []
    occupied: set[Coord] = set()

    for entry in ordered:
        if budget_ctx.remaining_budget_ms() <= 0:
            rejected.append(
                RimPlacementRejection(
                    candidate_id=entry.candidate.candidate_id,
                    equivalence_key=entry.candidate.equivalence_key,
                    reason=RimPlacementRejectReason.BUDGET_INTERRUPTED,
                )
            )
            continue

        cells = _occupied_cells(entry)
        conflict_cells = frozenset(cells & occupied)
        if conflict_cells:
            conflicting_id = _find_conflicting_selected(cells, tuple(selected))
            rejected.append(
                RimPlacementRejection(
                    candidate_id=entry.candidate.candidate_id,
                    equivalence_key=entry.candidate.equivalence_key,
                    reason=RimPlacementRejectReason.PHYSICAL_OVERLAP,
                    conflicting_candidate_id=conflicting_id,
                    conflicting_cells=conflict_cells,
                )
            )
            continue

        selected.append(entry)
        occupied |= set(cells)

    return tuple(selected), tuple(rejected)


__all__ = ["select_non_overlapping_candidates"]
