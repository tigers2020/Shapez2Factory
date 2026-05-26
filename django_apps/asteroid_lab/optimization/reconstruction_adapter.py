"""Reconstruction result -> OptimizationInput (RTTP PR-2; no shadow/RD imports)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    resolve_cell_transport_kind,
    resolve_default_asteroid_transport_kind,
    transport_kind_lookup_from_slice,
)
from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    ExistingTransportCell,
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.routing.exterior_connector_planner import (
    plan_exterior_connectors,
)
from django_apps.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    build_reconstruction_complete_map,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from django_apps.asteroid_lab.services.required_external_connectors import (
    required_external_connectors,
)
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile

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
    lookup = transport_kind_lookup_from_slice(catalog_slice) if catalog_slice is not None else None
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
            if kind is None:
                continue
        else:
            kind = _parse_transport_kind(cell.transport_kind)
            if kind is None:
                continue
        transport.append(ExistingTransportCell(coord=coord, transport_kind=kind))
    return frozenset(transport)


def partition_existing_transport(
    existing_transport: frozenset[ExistingTransportCell],
    active_kind: TransportKind,
) -> tuple[frozenset[Coord], frozenset[Coord], dict[str, int]]:
    """Same-kind trunk coords, wrong-kind blocked coords, mismatch counts by kind."""

    trunk: set[Coord] = set()
    blocked: set[Coord] = set()
    by_kind: dict[str, int] = {}
    for cell in existing_transport:
        if cell.transport_kind == active_kind:
            trunk.add(cell.coord)
        else:
            blocked.add(cell.coord)
            key = cell.transport_kind.value
            by_kind[key] = by_kind.get(key, 0) + 1
    return frozenset(trunk), frozenset(blocked), by_kind


def mismatched_existing_transport_metrics(
    blocked_incompatible: frozenset[Coord],
    *,
    by_kind: dict[str, int],
) -> dict[str, int | dict[str, int]]:
    """Output-only metrics for ``RTTP_ROUTE_DOMAIN`` (never solver input)."""

    return {
        "mismatched_existing_transport_count": len(blocked_incompatible),
        "mismatched_existing_transport_by_kind": dict(by_kind),
    }


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


def _resource_kind_for_transport(transport_kind: TransportKind) -> str:
    if transport_kind is TransportKind.FLUID_PIPE:
        return "fluid"
    return "shape"


def _max_asteroid_throughput_per_min(
    complete_map: ReconstructionCompleteMap,
    transport_kind: TransportKind,
) -> Decimal:
    envelope = build_reconstruction_capacity_envelope(complete_map=complete_map)
    resource = _resource_kind_for_transport(transport_kind)
    return Decimal(envelope["by_resource"][resource]["max_throughput_per_min"])


def _planned_exterior_route_goals(
    inp_partial: OptimizationInput,
    *,
    transport_kind: TransportKind,
    required_count: int,
) -> tuple[RouteGoal, ...]:
    plan = plan_exterior_connectors(
        inp_partial,
        required_count=required_count,
        transport_kind=transport_kind,
    )
    return plan.selected_goals


def _legacy_rim_adjacent_margin_route_goals(
    inp: OptimizationInput,
    *,
    transport_kind: TransportKind,
) -> tuple[RouteGoal, ...]:
    """Pre-EVTC margin flood when throughput implies zero required connectors."""

    seen: set[Coord] = set()
    goals: list[RouteGoal] = []
    for rim_cell in sorted(inp.rim_cells):
        for neighbor in neighbors4(rim_cell):
            if neighbor not in inp.external_void_cells or neighbor in seen:
                continue
            seen.add(neighbor)
            goals.append(
                RouteGoal(
                    coord=neighbor,
                    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
                    transport_kind=transport_kind,
                    priority=20,
                    existing_trunk=False,
                )
            )
    return tuple(goals)


def optimization_input_from_reconstruction(
    result: ReconstructionResult,
    *,
    cleanup: CleanupResult,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
    catalog_slice: BuildingCatalogSlice | None = None,
    complete_map: ReconstructionCompleteMap | None = None,
) -> OptimizationInput:
    """Map reconstruction-complete terrain to ``OptimizationInput`` (island-local ``x/y``)."""

    if complete_map is None:
        complete_map = build_reconstruction_complete_map(
            cleanup=cleanup,
            recon=result,
            coord_frame=coord_frame,
        )
    by_coord = _cells_by_coord(complete_map.cells)
    mineable = complete_map.field_cells
    external_void = complete_map.external_void_cells
    rim = _rim_cells(mineable)
    inner = mineable - rim
    existing_transport = _existing_transport(by_coord, catalog_slice=catalog_slice)
    if not existing_transport and catalog_slice is not None:
        transport_kind = resolve_default_asteroid_transport_kind(catalog_slice)
    else:
        transport_kind = _default_transport_kind(existing_transport)
    existing_trunk, blocked_incompatible, _mismatch_by_kind = partition_existing_transport(
        existing_transport, transport_kind
    )
    inp_partial = OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=external_void,
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=existing_trunk,
        transport_kind=transport_kind,
        route_goals=(),
        existing_transport_cells=existing_transport,
        blocked_incompatible_transport_cells=blocked_incompatible,
        coord_frame=coord_frame,
        catalog_slice=catalog_slice,
    )
    max_throughput = _max_asteroid_throughput_per_min(complete_map, transport_kind)
    required_count = required_external_connectors(
        max_asteroid_throughput_per_min=max_throughput,
        transport_kind=transport_kind,
    )
    if required_count <= 0:
        route_goals = _legacy_rim_adjacent_margin_route_goals(
            inp_partial,
            transport_kind=transport_kind,
        )
        evtc_required_count: int | None = None
    else:
        route_goals = _planned_exterior_route_goals(
            inp_partial,
            transport_kind=transport_kind,
            required_count=required_count,
        )
        evtc_required_count = required_count

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
        blocked_incompatible_transport_cells=blocked_incompatible,
        coord_frame=coord_frame,
        catalog_slice=catalog_slice,
        required_external_connector_count=evtc_required_count,
    )


__all__ = [
    "mismatched_existing_transport_metrics",
    "optimization_input_from_reconstruction",
    "partition_existing_transport",
]
