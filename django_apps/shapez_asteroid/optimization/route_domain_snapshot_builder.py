"""Single entry point for route_domain snapshots (Phase 1 / Phase 4)."""

from __future__ import annotations

from collections.abc import Mapping

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    ExistingTransportCell,
    OptimizationInput,
    RouteCellDomain,
)
from django_apps.shapez_asteroid.optimization.enums import RouteClass, TransportKind, TransportMask


def _mask_for_transport_cell(cell: ExistingTransportCell) -> TransportMask:
    if cell.transport_kind is TransportKind.SHAPE_BELT:
        return TransportMask.SHAPE_BELT
    if cell.transport_kind is TransportKind.FLUID_PIPE:
        return TransportMask.FLUID_PIPE
    return TransportMask.NONE


class RouteDomainSnapshotBuilder:
    """Builds immutable ``route_domain`` snapshots; callers must not mutate cells in-place."""

    @staticmethod
    def build_seed_snapshot(inp: OptimizationInput) -> dict[Coord, RouteCellDomain]:
        """Deterministic v0 seed from ``OptimizationInput`` (no probe / commit / replay input)."""

        transport_by_coord: dict[Coord, ExistingTransportCell] = {
            c.coord: c
            for c in sorted(inp.existing_transport_cells, key=lambda z: (z.coord.x, z.coord.y))
        }
        out: dict[Coord, RouteCellDomain] = {}
        for coord in inp.bbox.iter_cells():
            hard = coord in inp.blocked_cells
            if hard:
                out[coord] = RouteCellDomain(
                    coord=coord,
                    route_class=RouteClass.STANDARD,
                    traversal_cost=1,
                    hard_blocked=True,
                    carve_allowed=False,
                    transport_mask=TransportMask.NONE,
                )
                continue

            if coord in inp.protected_corridor_cells:
                out[coord] = RouteCellDomain(
                    coord=coord,
                    route_class=RouteClass.NARROW_CORRIDOR,
                    traversal_cost=2,
                    hard_blocked=False,
                    carve_allowed=False,
                    transport_mask=TransportMask.BOTH,
                )
                continue

            if coord in inp.existing_trunk_cells:
                cell = transport_by_coord.get(coord)
                mask = _mask_for_transport_cell(cell) if cell is not None else TransportMask.BOTH
                out[coord] = RouteCellDomain(
                    coord=coord,
                    route_class=RouteClass.PREFERRED_TRUNK,
                    traversal_cost=1,
                    hard_blocked=False,
                    carve_allowed=False,
                    transport_mask=mask,
                )
                continue

            etc = transport_by_coord.get(coord)
            if etc is not None:
                out[coord] = RouteCellDomain(
                    coord=coord,
                    route_class=RouteClass.STANDARD,
                    traversal_cost=2,
                    hard_blocked=False,
                    carve_allowed=False,
                    transport_mask=_mask_for_transport_cell(etc),
                )
                continue

            if coord in inp.asteroid_cells:
                carve = coord in inp.mineable_cells
                cost = 4 if coord in inp.rim_cells else 5
                out[coord] = RouteCellDomain(
                    coord=coord,
                    route_class=RouteClass.ASTEROID_CARVE if carve else RouteClass.STANDARD,
                    traversal_cost=cost,
                    hard_blocked=False,
                    carve_allowed=carve,
                    transport_mask=TransportMask.BOTH,
                )
                continue

            if coord in inp.external_void_cells:
                out[coord] = RouteCellDomain(
                    coord=coord,
                    route_class=RouteClass.STANDARD,
                    traversal_cost=2,
                    hard_blocked=False,
                    carve_allowed=False,
                    transport_mask=TransportMask.BOTH,
                )
                continue

            out[coord] = RouteCellDomain(
                coord=coord,
                route_class=RouteClass.STANDARD,
                traversal_cost=3,
                hard_blocked=False,
                carve_allowed=False,
                transport_mask=TransportMask.BOTH,
            )
        return out

    @staticmethod
    def build_snapshot(inp: OptimizationInput) -> Mapping[Coord, RouteCellDomain]:
        """Public API: seed snapshot (commit overlays are Sequence 7)."""

        return dict(RouteDomainSnapshotBuilder.build_seed_snapshot(inp))
