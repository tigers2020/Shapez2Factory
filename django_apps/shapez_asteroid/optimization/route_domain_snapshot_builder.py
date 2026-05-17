"""Single entry point for route_domain snapshots (Phase 1 / Phase 4)."""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    ExistingTransportCell,
    OptimizationInput,
    RouteCellDomain,
    RouteReservation,
)
from django_apps.shapez_asteroid.optimization.enums import (
    ReservationState,
    RouteClass,
    TransportKind,
    TransportMask,
)


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
    def build_commit_snapshot(
        inp: OptimizationInput,
        *,
        confirmed_reservations: tuple[RouteReservation, ...] = (),
        committed_occupied_cells: frozenset[Coord] = frozenset(),
    ) -> dict[Coord, RouteCellDomain]:
        """Sequence 6 overlay; delegates to :meth:`build_snapshot`."""

        return RouteDomainSnapshotBuilder.build_snapshot(
            inp,
            confirmed_reservations=confirmed_reservations,
            committed_occupied_cells=committed_occupied_cells,
        )

    @staticmethod
    def build_snapshot(
        inp: OptimizationInput,
        *,
        confirmed_reservations: tuple[RouteReservation, ...] = (),
        committed_occupied_cells: frozenset[Coord] = frozenset(),
    ) -> dict[Coord, RouteCellDomain]:
        """Canonical route_domain snapshot: seed, or seed plus commit overlays."""

        if not confirmed_reservations and not committed_occupied_cells:
            return RouteDomainSnapshotBuilder.build_seed_snapshot(inp)

        base = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
        for c in sorted(committed_occupied_cells, key=lambda z: (z.x, z.y)):
            cell = base.get(c)
            if cell is None:
                continue
            if c in inp.blocked_cells:
                continue
            base[c] = RouteCellDomain(
                coord=c,
                route_class=cell.route_class,
                traversal_cost=cell.traversal_cost,
                hard_blocked=True,
                carve_allowed=False,
                transport_mask=TransportMask.NONE,
            )

        confirmed_only = tuple(
            r
            for r in sorted(confirmed_reservations, key=lambda z: z.reservation_id)
            if r.reservation_state is ReservationState.CONFIRMED
        )
        for res in confirmed_only:
            mask_same = (
                TransportMask.SHAPE_BELT
                if res.transport_kind is TransportKind.SHAPE_BELT
                else TransportMask.FLUID_PIPE
            )
            for coord in res.path:
                if coord in inp.protected_corridor_cells:
                    continue
                if coord in inp.blocked_cells:
                    continue
                cell = base.get(coord)
                if cell is None:
                    continue
                if cell.hard_blocked and coord in committed_occupied_cells:
                    continue
                base[coord] = RouteCellDomain(
                    coord=coord,
                    route_class=RouteClass.PREFERRED_TRUNK,
                    traversal_cost=1,
                    hard_blocked=False,
                    carve_allowed=False,
                    transport_mask=mask_same,
                )
        return base
