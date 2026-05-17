"""RouteDomainSnapshotBuilder seed behavior (Sequence 1B)."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.shapez_asteroid.adapters.reconstruction_adapter import build_optimization_input
from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import ExistingTransportCell
from django_apps.shapez_asteroid.optimization.enums import TransportKind, TransportMask
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)

from .test_optimization_input import _cell, _snapshot


def test_protected_corridor_cells_are_route_domain_keys() -> None:
    cells = (
        _cell(1, 1, cell_kind="asteroid_shape_field", server_x=0, server_y=0),
        _cell(2, 1, cell_kind="asteroid_shape_field", server_x=1, server_y=0),
        _cell(1, 2, cell_kind="asteroid_shape_field", server_x=0, server_y=1),
        _cell(2, 2, cell_kind="asteroid_shape_field", server_x=1, server_y=1),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = reconstruct_snapshot(snap)
    protected = frozenset({Coord(3, 3)})
    inp = build_optimization_input(recon, cleanup, protected_corridor_cells=protected)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    for c in protected:
        assert c in domain
        assert domain[c].hard_blocked is False


def test_blocked_cells_are_hard_blocked_without_contradiction() -> None:
    cells = (
        _cell(1, 1, cell_kind="asteroid_shape_field", server_x=0, server_y=0),
        _cell(2, 1, cell_kind="asteroid_shape_field", server_x=1, server_y=0),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = reconstruct_snapshot(snap)
    blocked = frozenset({Coord(0, 0)})
    inp = build_optimization_input(recon, cleanup, blocked_cells=blocked)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    assert domain[Coord(0, 0)].hard_blocked is True
    assert domain[Coord(0, 0)].transport_mask.value == 0


def test_transport_mask_reflects_kind_not_strings() -> None:
    cells = (
        _cell(1, 0, cell_kind="space_belt", transport_kind="shape_belt", server_x=0, server_y=0),
        _cell(1, 1, cell_kind="asteroid_shape_field", server_x=0, server_y=1),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = reconstruct_snapshot(snap)
    et = frozenset({ExistingTransportCell(Coord(0, 0), TransportKind.SHAPE_BELT)})
    inp = build_optimization_input(recon, cleanup, existing_transport_cells=et)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cell = domain[Coord(0, 0)]
    assert cell.transport_mask == TransportMask.SHAPE_BELT
