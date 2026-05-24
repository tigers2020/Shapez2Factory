"""Reconstruction result -> OptimizationInput (RTTP PR-2; no shadow/RD imports)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    resolve_cell_transport_kind,
    resolve_default_asteroid_transport_kind,
    transport_kind_lookup_from_slice,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    ExistingTransportCell,
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile

_EXTERNAL_MARGIN_PRIORITY = 20
_TRANSPORT_CELL_KINDS = frozenset({"space_belt", "space_pipe"})


def _parse_transport_kind(raw: str) -> TransportKind | None:
    for member in TransportKind:
        if member.value == raw:
            return member
    return None


def _cells_by_coord(cells: tuple[DecodedCellDTO, ...]) -> dict[Coord, DecodedCellDTO]:
    return {(cell.x, cell.y): cell for cell in cells}


def _rim_cells(mineable: frozenset[Coord]) -> frozenset[Coord]:
    rim: set[Coord] = set()
    for coord in mineable:
        if any(neighbor not in mineable for neighbor in neighbors4(coord)):
            rim.add(coord)
    return frozenset(rim)


def _is_reconstruction_transport_cell(cell: DecodedCellDTO) -> bool:
    """Match reconstruction ``cell_kind`` to snapshot transport classifier."""

    return cell.cell_kind in _TRANSPORT_CELL_KINDS or is_transport_tile(cell)


def _existing_transport(
    by_coord: dict[Coord, DecodedCellDTO],
    *,
    catalog_slice: BuildingCatalogSlice | None = None,
) -> frozenset[ExistingTransportCell]:
    lookup = (
        transport_kind_lookup_from_slice(catalog_slice)
        if catalog_slice is not None
        else None
    )
    transport: list[ExistingTransportCell] = []
    for coord, cell in by_coord.items():
        if not _is_reconstruction_transport_cell(cell):
            continue
        if catalog_slice is not None:
            kind = resolve_cell_transport_kind(
                cell.transport_kind,
                catalog_slice=catalog_slice,
                lookup=lookup,
                coord=coord,
            )
        else:
            kind = _parse_transport_kind(cell.transport_kind)
            if kind is None:
                continue
        transport.append(ExistingTransportCell(coord=coord, transport_kind=kind))
    return frozenset(transport)


def _existing_trunk_cells(
    existing_transport: frozenset[ExistingTransportCell],
) -> frozenset[Coord]:
    """P1 map class: reconstruction transport coords seed skeleton trunk mask."""

    return frozenset(cell.coord for cell in existing_transport)


def _default_transport_kind(
    existing_transport: frozenset[ExistingTransportCell],
) -> TransportKind:
    if not existing_transport:
        return TransportKind.SHAPE_BELT
    shape_count = sum(
        1 for cell in existing_transport if cell.transport_kind is TransportKind.SHAPE_BELT
    )
    fluid_count = len(existing_transport) - shape_count
    if fluid_count > shape_count:
        return TransportKind.FLUID_PIPE
    return TransportKind.SHAPE_BELT


def _external_margin_route_goals(
    rim_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
    transport_kind: TransportKind,
) -> tuple[RouteGoal, ...]:
    seen: set[Coord] = set()
    goals: list[RouteGoal] = []
    for rim in sorted(rim_cells):
        for neighbor in neighbors4(rim):
            if neighbor not in external_void_cells or neighbor in seen:
                continue
            seen.add(neighbor)
            goals.append(
                RouteGoal(
                    coord=neighbor,
                    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
                    transport_kind=transport_kind,
                    priority=_EXTERNAL_MARGIN_PRIORITY,
                    existing_trunk=False,
                )
            )
    return tuple(goals)


def optimization_input_from_reconstruction(
    result: ReconstructionResult,
    *,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
    catalog_slice: BuildingCatalogSlice | None = None,
) -> OptimizationInput:
    """Map reconstruction topology to ``OptimizationInput`` using raw island ``x/y``."""

    topo = acceptance_topology_from_reconstruction(result, coord_frame=coord_frame)
    by_coord = _cells_by_coord(result.cells)
    mineable = topo.mineable_cells
    external_void = topo.external_void_cells
    rim = _rim_cells(mineable)
    inner = mineable - rim
    existing_transport = _existing_transport(by_coord, catalog_slice=catalog_slice)
    if not existing_transport and catalog_slice is not None:
        transport_kind = resolve_default_asteroid_transport_kind(catalog_slice)
    else:
        transport_kind = _default_transport_kind(existing_transport)
    existing_trunk = _existing_trunk_cells(existing_transport)
    route_goals = _external_margin_route_goals(rim, external_void, transport_kind)

    return OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=external_void,
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=existing_trunk,
        transport_kind=transport_kind,
        route_goals=route_goals,
        existing_transport_cells=existing_transport,
        coord_frame=coord_frame,
        catalog_slice=catalog_slice,
    )


__all__ = ["optimization_input_from_reconstruction"]
