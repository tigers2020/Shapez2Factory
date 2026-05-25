"""Derived FOT attach surface for outward rim transport (RTTP FOT PR-2)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def transport_attach_surface_cells(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
) -> frozenset[Coord]:
    return frozenset(inp.external_void_cells | skeleton.ring_cells)


def outward_dirs(
    anchor: Coord,
    output_dir: str,
    *,
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    domain: RouteCellDomain,  # noqa: ARG001 — reserved for PR-3 domain-aware outward scoring
) -> frozenset[str]:
    attach = transport_attach_surface_cells(inp, skeleton)
    goals = probe_goal_coords(inp, skeleton)
    outward: set[str] = set()
    for direction in ("N", "E", "S", "W"):
        unit = cardinal_unit_vector(CardinalDirection(direction))
        neighbor = (anchor[0] + unit[0], anchor[1] + unit[1])
        if neighbor in inp.mineable_cells:
            continue
        if neighbor in inp.blocked_incompatible_transport_cells:
            continue
        if neighbor in attach or neighbor in goals:
            outward.add(direction)
    if output_dir in outward:
        return frozenset({output_dir})
    return frozenset(outward)


__all__ = ["outward_dirs", "transport_attach_surface_cells"]
