"""F0 §3–§4: shareable trunk and reservation candidate cell policy (pure helpers)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.route_domain import RouteCellDomain


def build_elcp_base_cells(
    *,
    branch_cells: tuple[Coord, ...],
    new_trunk_cells: tuple[Coord, ...],
    reused_trunk_cells: tuple[Coord, ...],
) -> frozenset[Coord]:
    _ = reused_trunk_cells  # evidence only; MUST NOT enter base (F0 §3.2)
    return frozenset(branch_cells) | frozenset(new_trunk_cells)


def spine_delta_allowed_in_reservation(
    spine_delta_cells: frozenset[Coord],
    *,
    shareable_trunk_cells: frozenset[Coord],
    fl06_required_cells: frozenset[Coord],
) -> frozenset[Coord]:
    """SPINE-G3/G4: spine cells only when trunk-touch or FL-06 required."""

    return frozenset(
        cell
        for cell in spine_delta_cells
        if cell in shareable_trunk_cells or cell in fl06_required_cells
    )


def build_reservation_candidate_cells(
    *,
    stub_aligned_cells: frozenset[Coord],
    spine_delta_cells: frozenset[Coord],
    shareable_trunk_cells: frozenset[Coord],
    fl06_required_cells: frozenset[Coord],
) -> frozenset[Coord]:
    allowed_spine = spine_delta_allowed_in_reservation(
        spine_delta_cells,
        shareable_trunk_cells=shareable_trunk_cells,
        fl06_required_cells=fl06_required_cells,
    )
    return stub_aligned_cells | allowed_spine


def compute_elcp_reservation_candidate_cells(
    *,
    candidate: BundleCandidate,
    inp: OptimizationInput,
    domain: RouteCellDomain,
    branch_cells: tuple[Coord, ...],
    new_trunk_cells: tuple[Coord, ...],
    reused_trunk_cells: tuple[Coord, ...],
    shareable_at_commit: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
) -> frozenset[Coord] | None:
    """F0 §4 steps 2–5. Returns None when FL-06 rejects stub alignment."""

    from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
        _augment_route_cells_with_output_spine,
        _route_cells_with_required_output_stub,
    )

    base = build_elcp_base_cells(
        branch_cells=branch_cells,
        new_trunk_cells=new_trunk_cells,
        reused_trunk_cells=reused_trunk_cells,
    )
    stub_aligned = _route_cells_with_required_output_stub(
        candidate,
        base,
        domain,
        inp,
    )
    if stub_aligned is None:
        return None
    fl06_required = frozenset(stub_aligned - base)
    augmented = _augment_route_cells_with_output_spine(
        candidate,
        base,
        domain,
        committed_route_cells=committed_route_cells,
        shareable_trunk_cells=shareable_at_commit,
    )
    spine_delta = frozenset(augmented - base)
    return build_reservation_candidate_cells(
        stub_aligned_cells=stub_aligned,
        spine_delta_cells=spine_delta,
        shareable_trunk_cells=shareable_at_commit,
        fl06_required_cells=fl06_required | frozenset(stub_aligned),
    )


__all__ = [
    "build_elcp_base_cells",
    "build_reservation_candidate_cells",
    "compute_elcp_reservation_candidate_cells",
    "spine_delta_allowed_in_reservation",
]
