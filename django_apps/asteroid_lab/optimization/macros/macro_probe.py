"""Macro-level shared lift/trunk route probe (RTTP v1 MacroBundleT3, PR-B)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.macros.macro_dtos import SharedLiftStubPlan
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route


@dataclass(frozen=True, slots=True)
class MacroProbeResult:
    reachable: bool
    cost: int
    expanded_nodes: int


def _platform_coord_for_plan(
    domain: RouteCellDomain,
    plan: SharedLiftStubPlan,
) -> tuple[int, int] | None:
    for edge in domain.lift_edges:
        if edge.platform_coord in plan.lift_column_coords:
            return edge.platform_coord
    return None


def probe_macro_shared_lift(
    domain: RouteCellDomain,
    plan: SharedLiftStubPlan,
    *,
    max_expansions: int = 500,
) -> MacroProbeResult:
    """Validate platform → lift → ``trunk_entry_coord`` on a static route domain."""

    if not plan.lift_column_coords or plan.trunk_entry_coord is None:
        return MacroProbeResult(reachable=False, cost=0, expanded_nodes=0)

    platform = _platform_coord_for_plan(domain, plan)
    if platform is None:
        return MacroProbeResult(reachable=False, cost=0, expanded_nodes=0)

    goals = frozenset({plan.trunk_entry_coord})
    probe = probe_route(domain, platform, goals, max_expansions=max_expansions)
    return MacroProbeResult(
        reachable=probe.reachable,
        cost=probe.cost,
        expanded_nodes=probe.expanded_nodes,
    )


__all__ = ["MacroProbeResult", "probe_macro_shared_lift"]
