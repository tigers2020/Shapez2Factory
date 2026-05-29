"""Test helpers for Layer 04 placement (not algorithm input)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind


def succeeded_probe_at(
    anchor: tuple[int, int],
    *,
    rank: int = 1,
    gene_key: str = "miner_seed_m3e_01",
    equivalence_key: str = "equiv_a",
    mining: frozenset[tuple[int, int]] | None = None,
    transport: frozenset[tuple[int, int]] | None = None,
    goal: tuple[int, int] = (8, 4),
    output_dir: Direction = Direction.E,
    rotation: int | None = None,
    route_cost: int = 0,
) -> RouteProbedBundleCandidate:
    if rotation is None:
        rotation = {
            Direction.E: 0,
            Direction.S: 1,
            Direction.W: 2,
            Direction.N: 3,
        }[output_dir]
    stub_start = (anchor[0] + 1, anchor[1]) if transport is None else min(transport)
    candidate = make_bundle_candidate_for_test(
        gene_key=gene_key,
        intrinsic_priority_rank=rank,
        anchor_coord=anchor,
        equivalence_key=equivalence_key,
        output_dir=output_dir,
        rotation=rotation,
        mining_occupied_cells=mining or frozenset({anchor}),
        transport_stub_cells=transport or frozenset({stub_start}),
        route_probe_start_coord=stub_start,
    )
    path = (stub_start, goal)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=goal,
            path_coords=path,
            steps_expanded=len(path),
            transport_kind=TransportKind.SHAPE_BELT,
            route_cost=route_cost,
        ),
        route_goal_id="ext_conn_00",
        reject_reason=None,
    )
