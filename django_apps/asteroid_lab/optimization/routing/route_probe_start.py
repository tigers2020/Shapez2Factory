"""Shared route probe start resolution (RTTP FOT PR-2)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import RouteProbeStartPolicy
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.routing.route_probe import initial_phase


def resolve_route_probe_start(
    *,
    anchor_coord: Coord,
    output_stub: Coord,
    domain: RouteCellDomain,
    policy: RouteProbeStartPolicy,
) -> Coord | None:
    if output_stub not in domain.blocked_cells and initial_phase(domain, output_stub) is not None:
        return output_stub
    if policy is RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED:
        if initial_phase(domain, anchor_coord) == "platform":
            return anchor_coord
    return None


__all__ = ["resolve_route_probe_start"]
