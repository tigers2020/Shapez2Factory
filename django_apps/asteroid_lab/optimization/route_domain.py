"""Route cell domain snapshot builder (Phase 1 + Phase 4 seed, Phase 7 API)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import RouteClass, TransportKind, TransportMask
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    OptimizationInput,
    RouteReservation,
)


@dataclass(frozen=True, slots=True)
class RouteCellDomain:
    """Per-cell routing policy (Phase 4)."""

    coord: Coord
    route_class: RouteClass
    traversal_cost: int
    hard_blocked: bool
    carve_allowed: bool
    transport_mask: TransportMask


def _mask_for_transport_kind(tk: TransportKind) -> TransportMask:
    if tk == TransportKind.SHAPE_BELT:
        return TransportMask.SHAPE_BELT
    if tk == TransportKind.FLUID_PIPE:
        return TransportMask.FLUID_PIPE
    return TransportMask.NONE


def _iter_bbox_cells(bb: BBox) -> list[Coord]:
    out: list[Coord] = []
    for sx in range(bb.min_sx, bb.max_sx + 1):
        for sy in range(bb.min_sy, bb.max_sy + 1):
            out.append((sx, sy))
    return out


def _build_seed_cells(inp: OptimizationInput) -> dict[Coord, RouteCellDomain]:
    transport_by_coord: dict[Coord, TransportKind] = {
        c.coord: c.transport_kind for c in inp.existing_transport_cells
    }

    out: dict[Coord, RouteCellDomain] = {}
    for coord in _iter_bbox_cells(inp.bbox):
        if coord in inp.blocked_cells:
            out[coord] = RouteCellDomain(
                coord=coord,
                route_class=RouteClass.BLOCKED,
                traversal_cost=1,
                hard_blocked=True,
                carve_allowed=False,
                transport_mask=TransportMask.NONE,
            )
            continue
        if coord in inp.protected_corridor_cells:
            out[coord] = RouteCellDomain(
                coord=coord,
                route_class=RouteClass.CORRIDOR_PROTECTED,
                traversal_cost=1,
                hard_blocked=False,
                carve_allowed=False,
                transport_mask=TransportMask.BOTH,
            )
            continue
        if coord in inp.existing_trunk_cells:
            out[coord] = RouteCellDomain(
                coord=coord,
                route_class=RouteClass.TRUNK,
                traversal_cost=1,
                hard_blocked=False,
                carve_allowed=False,
                transport_mask=TransportMask.BOTH,
            )
            continue
        tk = transport_by_coord.get(coord)
        if tk is not None and tk != TransportKind.NONE:
            out[coord] = RouteCellDomain(
                coord=coord,
                route_class=RouteClass.TRANSPORT,
                traversal_cost=1,
                hard_blocked=False,
                carve_allowed=False,
                transport_mask=_mask_for_transport_kind(tk),
            )
            continue
        if coord in inp.mineable_cells:
            out[coord] = RouteCellDomain(
                coord=coord,
                route_class=RouteClass.ASTEROID,
                traversal_cost=1,
                hard_blocked=False,
                carve_allowed=True,
                transport_mask=TransportMask.BOTH,
            )
            continue
        if coord in inp.external_void_cells:
            out[coord] = RouteCellDomain(
                coord=coord,
                route_class=RouteClass.VOID_EXTERNAL,
                traversal_cost=1,
                hard_blocked=False,
                carve_allowed=False,
                transport_mask=TransportMask.BOTH,
            )
            continue
        out[coord] = RouteCellDomain(
            coord=coord,
            route_class=RouteClass.VOID_EXTERNAL,
            traversal_cost=1,
            hard_blocked=False,
            carve_allowed=False,
            transport_mask=TransportMask.BOTH,
        )
    return out


def _apply_blocked_overlay(
    cells: dict[Coord, RouteCellDomain],
    blocked: frozenset[Coord],
) -> dict[Coord, RouteCellDomain]:
    if not blocked:
        return cells
    out = dict(cells)
    for coord in blocked:
        if coord not in out:
            continue
        out[coord] = RouteCellDomain(
            coord=coord,
            route_class=RouteClass.BLOCKED,
            traversal_cost=1,
            hard_blocked=True,
            carve_allowed=False,
            transport_mask=TransportMask.NONE,
        )
    return out


def _apply_reservation_overlay(
    cells: dict[Coord, RouteCellDomain],
    reservations: tuple[RouteReservation, ...],
) -> dict[Coord, RouteCellDomain]:
    if not reservations:
        return cells

    reserved_kind: dict[Coord, TransportKind] = {}
    for res in reservations:
        for coord in res.reserved_cells:
            prev = reserved_kind.get(coord)
            if prev is not None and prev != res.transport_kind:
                reserved_kind[coord] = res.transport_kind
            else:
                reserved_kind[coord] = res.transport_kind

    out = dict(cells)
    for coord, tk in reserved_kind.items():
        if coord not in out:
            continue
        cell = out[coord]
        if cell.hard_blocked:
            continue
        out[coord] = RouteCellDomain(
            coord=coord,
            route_class=RouteClass.TRANSPORT,
            traversal_cost=1,
            hard_blocked=False,
            carve_allowed=False,
            transport_mask=_mask_for_transport_kind(tk),
        )
    return out


def optimization_input_cache_key(inp: OptimizationInput) -> tuple[object, ...]:
    transport_sig = tuple(
        sorted((cell.coord, cell.transport_kind) for cell in inp.existing_transport_cells)
    )
    return (
        inp.bbox,
        inp.blocked_cells,
        inp.protected_corridor_cells,
        inp.existing_trunk_cells,
        transport_sig,
        inp.mineable_cells,
        inp.external_void_cells,
    )


_SEED_DOMAIN_CACHE: dict[tuple[object, ...], dict[Coord, RouteCellDomain]] = {}


def clear_seed_domain_cache() -> None:
    """Clear cached seed domains (tests / run boundaries)."""

    _SEED_DOMAIN_CACHE.clear()


def _cached_seed_cells(inp: OptimizationInput) -> dict[Coord, RouteCellDomain]:
    key = optimization_input_cache_key(inp)
    cached = _SEED_DOMAIN_CACHE.get(key)
    if cached is None:
        cached = _build_seed_cells(inp)
        _SEED_DOMAIN_CACHE[key] = cached
    return cached


class RouteDomainSnapshotBuilder:
    """Single entry point for ``route_domain`` snapshots (Phase 1 / 7)."""

    @staticmethod
    def build_seed_snapshot(inp: OptimizationInput) -> dict[Coord, RouteCellDomain]:
        """Cached immutable seed cells (no overlays)."""

        return dict(_cached_seed_cells(inp))

    @staticmethod
    def build_snapshot(
        inp: OptimizationInput,
        *,
        confirmed_reservations: tuple[RouteReservation, ...] = (),
        committed_occupied_cells: frozenset[Coord] = frozenset(),
        provisional_blocked_cells: frozenset[Coord] = frozenset(),
    ) -> dict[Coord, RouteCellDomain]:
        """Immutable ``Coord -> RouteCellDomain`` map for probe/commit (v0)."""

        blocked_for_probe = committed_occupied_cells | provisional_blocked_cells
        base = dict(_cached_seed_cells(inp))
        with_blocked = _apply_blocked_overlay(base, blocked_for_probe)
        return _apply_reservation_overlay(with_blocked, confirmed_reservations)


def assert_seed_domain_consistent(
    inp: OptimizationInput, domain: dict[Coord, RouteCellDomain]
) -> None:
    """Debug helper: ``blocked_cells`` must imply ``hard_blocked`` in the seed snapshot."""

    for c in inp.blocked_cells:
        cell = domain.get(c)
        assert cell is not None
        assert cell.hard_blocked is True
