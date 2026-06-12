"""Commit-time route re-probe helpers shared by beam selection and finalize."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeStatus,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_domain_snapshot_builder import (  # noqa: E501
    RouteDomainSnapshotBuilder,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    build_layer03_route_goals,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.application.asteroid_lab.layers.shared.route_probe import (
    RouteProbeLimits,
    resolve_layer03_route_probe_limits,
    weighted_route_probe,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import BBox, Coord, bbox_from_coords
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


@dataclass(frozen=True, slots=True)
class CommitDomainState:
    """Cumulative equipment + reserved corridors after commit-time re-probes."""

    occupied: frozenset[Coord] = frozenset()
    corridor: frozenset[Coord] = frozenset()


@dataclass(frozen=True, slots=True)
class CommitReprobeContext:
    """Shared route-domain inputs for finalize and commit-aware beam selection."""

    route_goals: tuple[RouteGoal, ...]
    search_bbox: BBox
    base_walkable: frozenset[Coord]
    field_cells: frozenset[Coord]
    probe_limits: RouteProbeLimits


def _build_route_goals(exterior_plan: ExteriorConnectionPlan) -> tuple[RouteGoal, ...]:
    return build_layer03_route_goals(
        exterior_plan, transport_kind=TransportKind.SPACE_BELT
    ) + build_layer03_route_goals(exterior_plan, transport_kind=TransportKind.SPACE_PIPE)


def build_commit_reprobe_context(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan,
) -> CommitReprobeContext | None:
    field_cells = complete_map.field_cells
    base_walkable = field_cells | complete_map.external_void_cells
    if not base_walkable:
        return None
    search_bbox = bbox_from_coords(base_walkable)
    return CommitReprobeContext(
        route_goals=_build_route_goals(exterior_plan),
        search_bbox=search_bbox,
        base_walkable=frozenset(base_walkable),
        field_cells=frozenset(field_cells),
        probe_limits=resolve_layer03_route_probe_limits(search_bbox=search_bbox),
    )


def try_commit_reprobe(
    *,
    ctx: CommitReprobeContext,
    state: CommitDomainState,
    probed: RouteProbedBundleCandidate,
) -> tuple[bool, CommitDomainState, tuple[Coord, ...]]:
    """Return whether a bundle survives commit-time re-probe, the updated domain, and path."""

    cand = probed.candidate
    own_equipment = cand.mining_occupied_cells | cand.transport_stub_cells
    if state.occupied & set(own_equipment):
        return False, state, ()
    # Equipment overlap is the only hard blocker. Corridor cells are accumulated for
    # overlay / observability and soft fitness pressure, not exclusive void-lane blocking
    # (CANON: many miners may merge toward one saturated exterior belt connector).
    blockers = frozenset(state.occupied | set(own_equipment))
    domain = RouteDomainSnapshotBuilder.build_snapshot(
        search_bbox=ctx.search_bbox,
        base_walkable=ctx.base_walkable,
        field_cells=ctx.field_cells,
        blockers=blockers,
    )
    reprobed = weighted_route_probe(
        candidate=cand,
        route_goals=ctx.route_goals,
        domain=domain,
        field_cells=ctx.field_cells,
        probe_limits=ctx.probe_limits,
    )
    if reprobed.route_probe_status != RouteProbeStatus.SUCCEEDED or (
        reprobed.route_probe_result is None
    ):
        return False, state, ()
    path = reprobed.route_probe_result.path_coords
    return (
        True,
        CommitDomainState(
            occupied=state.occupied | frozenset(own_equipment),
            corridor=state.corridor | (frozenset(path) - frozenset(own_equipment)),
        ),
        path,
    )


__all__ = [
    "CommitDomainState",
    "CommitReprobeContext",
    "build_commit_reprobe_context",
    "try_commit_reprobe",
]
