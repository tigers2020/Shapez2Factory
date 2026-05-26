"""EVTC-4 — external void traversable in route domain."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def test_void_cells_traversable_when_in_external_void(greenfield_optimization_input) -> None:
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)
    void_coord = next(iter(inp.external_void_cells))
    assert void_coord in domain.traversable_cells
    assert void_coord not in domain.blocked_cells
