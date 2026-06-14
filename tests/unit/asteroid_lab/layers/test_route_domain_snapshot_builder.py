"""RouteDomainSnapshotBuilder contract tests."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.route_domain_snapshot_builder import (  # noqa: E501
    RouteDomainSnapshotBuilder,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import bbox_from_coords


def test_build_snapshot_keeps_walkable_reference_and_blocks_in_step_cost() -> None:
    base = frozenset({(0, 0), (1, 0), (0, 1)})
    field = frozenset({(1, 0)})
    blockers = frozenset({(0, 0)})
    bbox = bbox_from_coords(base)

    domain = RouteDomainSnapshotBuilder.build_snapshot(
        search_bbox=bbox,
        base_walkable=base,
        field_cells=field,
        blockers=blockers,
    )

    assert domain.blocked_cells == blockers
    assert domain.walkable_cells == base
    assert domain.field_cost_cells == field
    assert domain.step_cost((0, 0)) is None
    assert domain.step_cost((1, 0)) == 25
    assert domain.step_cost((0, 1)) == 1


def test_build_immediate_probe_surface_uses_placeable_only() -> None:
    placeable = frozenset({(2, 3)})
    domain = RouteDomainSnapshotBuilder.build_immediate_probe_surface(
        placeable_cells=placeable,
    )
    assert domain.walkable_cells == placeable
    assert domain.blocked_cells == frozenset()
    assert domain.field_cost_cells == frozenset()
