"""RTTP lift/lane route domain — RTTP-G5 prep (PR-2)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
    path_exists_via_lift,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def test_lift_edge_connects_stub_to_trunk_mask(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)

    assert skeleton.lift_columns, "expected at least one lift column on greenfield rim"
    assert skeleton.ring_ports, "expected ring ports on greenfield skeleton"

    column = skeleton.lift_columns[0]
    start = column.platform_coord
    ring_port_goals = frozenset(port.coord for port in skeleton.ring_ports)

    assert start in inp.rim_cells
    assert column.lift_coord in domain.trunk_mask_cells
    for neighbor in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        adjacent = (start[0] + neighbor[0], start[1] + neighbor[1])
        if adjacent == column.lift_coord:
            continue
        if adjacent in inp.inner_cells:
            assert adjacent in domain.blocked_cells

    assert path_exists_via_lift(domain, start, ring_port_goals)
