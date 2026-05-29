"""Build RimBundlePlacement and ProvisionalLayoutOverlay from probed candidates."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCellRole,
    BundlePlacement,
    RouteProbedBundleCandidate,
)
from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
    ProvisionalPlacedCell,
)
from django_apps.asteroid_lab.layers.contracts.rim_placement import RimBundlePlacement
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def _cells_for_role(
    placements: tuple[BundlePlacement, ...],
    role: BundleCellRole,
) -> frozenset[Coord]:
    return frozenset(p.coord for p in placements if p.cell_role is role)


def build_rim_bundle_placement(entry: RouteProbedBundleCandidate) -> RimBundlePlacement:
    candidate = entry.candidate
    placements = candidate.placements
    extractor = _cells_for_role(placements, BundleCellRole.MINER)
    extension = _cells_for_role(placements, BundleCellRole.EXTENSION)
    output_stub = _cells_for_role(placements, BundleCellRole.TRANSPORT_STUB)
    occupied = candidate.mining_occupied_cells | candidate.transport_stub_cells

    goal_cells: frozenset[Coord] = frozenset()
    if entry.route_probe_result is not None and entry.route_probe_result.goal_coord is not None:
        goal_cells = frozenset({entry.route_probe_result.goal_coord})

    placement_id = f"{candidate.candidate_id}:prov"
    return RimBundlePlacement(
        candidate_id=candidate.candidate_id,
        placement_id=placement_id,
        equivalence_key=candidate.equivalence_key,
        gene_key=candidate.gene_key,
        anchor_coord=candidate.anchor_coord,
        transport_kind=candidate.transport_kind,
        resource_kind=candidate.resource_kind,
        occupied_cells=occupied,
        extractor_cells=extractor,
        extension_cells=extension,
        output_stub_cells=output_stub,
        route_probe_goal_cells=goal_cells,
        placement_state=PlacementCommitState.PROVISIONAL_PLACED,
        intrinsic_priority_rank=candidate.intrinsic_priority_rank,
    )


def build_provisional_overlay(
    placements: tuple[RimBundlePlacement, ...],
) -> ProvisionalLayoutOverlay:
    if not placements:
        return ProvisionalLayoutOverlay.empty()

    by_cell: dict[Coord, ProvisionalPlacedCell] = {}
    extractor: set[Coord] = set()
    extension: set[Coord] = set()
    transport_stub: set[Coord] = set()
    occupied: set[Coord] = set()

    for placement in placements:
        candidate = placement.candidate_id
        for coord in placement.extractor_cells:
            extractor.add(coord)
            occupied.add(coord)
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=candidate,
                placement_id=placement.placement_id,
                role=BundleCellRole.MINER,
                transport_kind=placement.transport_kind,
                placement_state=PlacementCommitState.PROVISIONAL_PLACED,
            )
        for coord in placement.extension_cells:
            extension.add(coord)
            occupied.add(coord)
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=candidate,
                placement_id=placement.placement_id,
                role=BundleCellRole.EXTENSION,
                transport_kind=placement.transport_kind,
                placement_state=PlacementCommitState.PROVISIONAL_PLACED,
            )
        for coord in placement.output_stub_cells:
            transport_stub.add(coord)
            occupied.add(coord)
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=candidate,
                placement_id=placement.placement_id,
                role=BundleCellRole.TRANSPORT_STUB,
                transport_kind=placement.transport_kind,
                placement_state=PlacementCommitState.PROVISIONAL_PLACED,
            )

    return ProvisionalLayoutOverlay(
        occupied_cells=frozenset(occupied),
        extractor_cells=frozenset(extractor),
        extension_cells=frozenset(extension),
        transport_stub_cells=frozenset(transport_stub),
        by_cell=by_cell,
    )


__all__ = ["build_provisional_overlay", "build_rim_bundle_placement"]
