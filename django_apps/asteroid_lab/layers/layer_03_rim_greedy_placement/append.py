"""Map committed rim greedy placements to append result (transform only; no validation)."""

from __future__ import annotations

from collections.abc import Sequence

from django_apps.asteroid_lab.layers.contracts.candidates import BundleCellRole
from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
    ProvisionalPlacedCell,
)
from django_apps.asteroid_lab.layers.contracts.rim_greedy import (
    LAYER_03_GREEDY_SOURCE,
    CommittedRimSeedPlacement,
)
from django_apps.asteroid_lab.layers.contracts.rim_greedy_append import (
    APPEND_CELL_KIND_PRIORITY,
    LAYER_03_APPEND_SOURCE,
    AppendCellKind,
    AppendedPlacementCell,
    Layer03AppendResult,
    build_empty_layer03_append_result,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_KIND_PRIORITY_RANK = {kind: index for index, kind in enumerate(APPEND_CELL_KIND_PRIORITY)}

_APPEND_TO_BUNDLE_ROLE: dict[AppendCellKind, BundleCellRole] = {
    AppendCellKind.MINER: BundleCellRole.MINER,
    AppendCellKind.EXTENSION: BundleCellRole.EXTENSION,
    AppendCellKind.OUTPUT_STUB: BundleCellRole.TRANSPORT_STUB,
    AppendCellKind.ROUTE_RESERVED: BundleCellRole.ROUTE_RESERVED,
}


def _emit_cell(
    collapsed: dict[Coord, AppendedPlacementCell],
    *,
    coord: Coord,
    kind: AppendCellKind,
    placement_id: str,
    variant_id: str,
) -> None:
    cell = AppendedPlacementCell(
        coord=coord,
        kind=kind,
        placement_id=placement_id,
        variant_id=variant_id,
        source_layer=LAYER_03_APPEND_SOURCE,
    )
    existing = collapsed.get(coord)
    if existing is None:
        collapsed[coord] = cell
        return
    if _KIND_PRIORITY_RANK[kind] < _KIND_PRIORITY_RANK[existing.kind]:
        collapsed[coord] = cell


def append_committed_rim_placements(
    *,
    committed_placements: Sequence[CommittedRimSeedPlacement],
) -> Layer03AppendResult:
    """Transform committed placements to appended cells; no replay or route validation."""

    if not committed_placements:
        return build_empty_layer03_append_result()

    collapsed: dict[Coord, AppendedPlacementCell] = {}
    for placement in committed_placements:
        pid = placement.placement_id
        vid = placement.variant_id
        for coord in sorted(placement.miner_cells):
            _emit_cell(
                collapsed,
                coord=coord,
                kind=AppendCellKind.MINER,
                placement_id=pid,
                variant_id=vid,
            )
        for coord in sorted(placement.extension_cells):
            _emit_cell(
                collapsed,
                coord=coord,
                kind=AppendCellKind.EXTENSION,
                placement_id=pid,
                variant_id=vid,
            )
        _emit_cell(
            collapsed,
            coord=placement.m_output_stub,
            kind=AppendCellKind.OUTPUT_STUB,
            placement_id=pid,
            variant_id=vid,
        )
        for coord in placement.route_probe_path:
            _emit_cell(
                collapsed,
                coord=coord,
                kind=AppendCellKind.ROUTE_RESERVED,
                placement_id=pid,
                variant_id=vid,
            )

    cells = tuple(collapsed[coord] for coord in sorted(collapsed.keys()))
    route_reserved_cell_count = sum(
        1 for cell in cells if cell.kind is AppendCellKind.ROUTE_RESERVED
    )
    return Layer03AppendResult(
        cells=cells,
        placement_count=len(committed_placements),
        route_reserved_cell_count=route_reserved_cell_count,
        source_layer=LAYER_03_APPEND_SOURCE,
    )


def provisional_overlay_from_append(
    append_result: Layer03AppendResult,
    *,
    transport_kind: TransportKind,
) -> ProvisionalLayoutOverlay:
    """Single mapper: append cells → provisional overlay (equipment, stub, reserved route)."""

    by_cell: dict[Coord, ProvisionalPlacedCell] = {}
    for appended in append_result.cells:
        role = _APPEND_TO_BUNDLE_ROLE[appended.kind]
        by_cell[appended.coord] = ProvisionalPlacedCell(
            coord=appended.coord,
            candidate_id=appended.placement_id,
            placement_id=appended.placement_id,
            role=role,
            transport_kind=transport_kind,
            placement_state=PlacementCommitState.PROVISIONAL_PLACED,
        )
    occupied = frozenset(by_cell.keys())
    extractors = frozenset(c for c, cell in by_cell.items() if cell.role is BundleCellRole.MINER)
    extensions = frozenset(
        c for c, cell in by_cell.items() if cell.role is BundleCellRole.EXTENSION
    )
    stubs = frozenset(
        c for c, cell in by_cell.items() if cell.role is BundleCellRole.TRANSPORT_STUB
    )
    return ProvisionalLayoutOverlay(
        occupied_cells=occupied,
        extractor_cells=extractors,
        extension_cells=extensions,
        transport_stub_cells=stubs,
        by_cell=by_cell,
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


__all__ = [
    "append_committed_rim_placements",
    "provisional_overlay_from_append",
]
