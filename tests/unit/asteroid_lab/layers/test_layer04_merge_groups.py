"""Route group registry — union-find capacity (PR-L4-3)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.merge_groups import (
    RouteGroupRegistry,
)


def test_two_connectors_merged_capacity_24_shape() -> None:
    reg = RouteGroupRegistry(unit_capacity_m=12, transport_kind=TransportKind.SHAPE_BELT)
    left = reg.connector_group("c0")
    right = reg.connector_group("c1")
    root = reg.union(left, right)
    assert reg.capacity_m(root) == 24
    assert reg.remaining_m(root) == 24


def test_shared_trunk_cell_unions_connector_groups() -> None:
    reg = RouteGroupRegistry(unit_capacity_m=12, transport_kind=TransportKind.SHAPE_BELT)
    g0 = reg.commit_path(
        path=((0, 0), (1, 0)),
        placement_id="p0",
        connector_id="c0",
        source_load_m=4,
    )
    g1 = reg.commit_path(
        path=((1, 0), (2, 0)),
        placement_id="p1",
        connector_id="c1",
        source_load_m=4,
    )
    assert reg.find(g0) == reg.find(g1)
    assert reg.capacity_m(g0) == 24
    assert reg.remaining_m(g0) == 16


def test_group_at_cell_returns_merged_root() -> None:
    reg = RouteGroupRegistry(unit_capacity_m=12, transport_kind=TransportKind.SHAPE_BELT)
    reg.commit_path(
        path=((0, 0), (1, 0)),
        placement_id="p0",
        connector_id="c0",
        source_load_m=4,
    )
    gid = reg.group_at_cell((1, 0))
    assert gid is not None
    assert reg.remaining_m(gid) == 8
