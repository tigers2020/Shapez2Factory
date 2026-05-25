"""Atomic macro commit (three child bundles per genome slot, RTTP v1 PR-E)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitDomainState,
    CommitResult,
    _rebuild_domain,
    incremental_commit,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.macros.macro_dtos import MacroBundleCandidate
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


@dataclass(frozen=True, slots=True)
class MacroCommitResult:
    committed_macro_ids: tuple[str, ...]
    committed_child_ids: tuple[str, ...]
    reserved_route_cells: frozenset[Coord]
    domain_version: int
    conflicts: tuple[CommitConflict, ...]


def _domain_after_single_commit(
    domain: CommitDomainState,
    candidate: BundleCandidate,
    result: CommitResult,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
) -> CommitDomainState:
    committed_occupied = frozenset(domain.committed_occupied | candidate.occupied_cells)
    committed_fixed_output_transport_cells = frozenset(
        domain.committed_fixed_output_transport_cells
        | {fixed_output_transport_cell(candidate)}
    )
    committed_route_cells = result.reserved_route_cells
    return CommitDomainState(
        domain=_rebuild_domain(
            skeleton,
            inp,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
        ),
        version=result.domain_version,
        committed_route_cells=committed_route_cells,
        committed_occupied=committed_occupied,
        committed_fixed_output_transport_cells=committed_fixed_output_transport_cells,
        trunk_mask_cells=frozenset(domain.trunk_mask_cells | committed_route_cells),
    )


def incremental_commit_macro(
    genome: PlacementGenome,
    macros_by_id: dict[str, MacroBundleCandidate],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    *,
    domain: CommitDomainState,
) -> MacroCommitResult:
    """Commit each macro slot atomically (all three children or none)."""

    committed_macro_ids: list[str] = []
    committed_child_ids: list[str] = []
    conflicts: list[CommitConflict] = []
    current = domain

    for macro_id in genome.commit_order:
        macro_row = macros_by_id.get(macro_id)
        if macro_row is None:
            conflicts.append(
                CommitConflict(
                    candidate_id=macro_id,
                    reason=CommitConflictReason.CANDIDATE_NOT_FOUND,
                )
            )
            continue

        macro_start = current
        slot_child_ids: list[str] = []
        macro_failed = False

        for child in macro_row.macro.children:
            single = incremental_commit(
                PlacementGenome(commit_order=(child.candidate_id,)),
                candidates_by_id,
                inp,
                skeleton,
                domain=current,
            )
            if single.conflicts:
                conflicts.append(
                    CommitConflict(
                        candidate_id=macro_id,
                        reason=single.conflicts[0].reason,
                    )
                )
                macro_failed = True
                break
            if child.candidate_id not in single.committed_ids:
                conflicts.append(
                    CommitConflict(
                        candidate_id=macro_id,
                        reason=CommitConflictReason.MACRO_CHILD_CONFLICT,
                    )
                )
                macro_failed = True
                break
            slot_child_ids.append(child.candidate_id)
            current = _domain_after_single_commit(
                current,
                child,
                single,
                skeleton,
                inp,
            )

        if macro_failed:
            current = macro_start
            continue

        committed_macro_ids.append(macro_id)
        committed_child_ids.extend(slot_child_ids)

    return MacroCommitResult(
        committed_macro_ids=tuple(committed_macro_ids),
        committed_child_ids=tuple(committed_child_ids),
        reserved_route_cells=current.committed_route_cells,
        domain_version=current.version,
        conflicts=tuple(conflicts),
    )


__all__ = ["MacroCommitResult", "incremental_commit_macro"]
