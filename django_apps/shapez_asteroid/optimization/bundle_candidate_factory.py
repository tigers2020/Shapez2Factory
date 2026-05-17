"""Factory for ``BundleCandidate`` success contract (Sequence 3)."""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import BundleCandidate, RouteProbeResult
from django_apps.shapez_asteroid.optimization.enums import CardinalDirection, TransportKind


def make_reachable_bundle_candidate(
    *,
    candidate_id: str,
    pattern_id: str,
    topology_signature: str,
    extractor: Coord,
    extensions: tuple[Coord, ...],
    occupied_cells: frozenset[Coord],
    output_stub: Coord,
    output_dir: CardinalDirection,
    transport_kind: TransportKind,
    base_throughput: int,
    base_score: float,
    route_probe_result: RouteProbeResult,
) -> BundleCandidate:
    """Centralized assertions for normal-pool route probe invariants."""

    if not route_probe_result.reachable:
        raise ValueError("BundleCandidate requires reachable route_probe_result")
    if route_probe_result.reached_goal is None:
        raise ValueError("BundleCandidate requires non-None reached_goal when reachable")
    if route_probe_result.failure_reason is not None:
        raise ValueError("reachable BundleCandidate must have failure_reason None")
    return BundleCandidate(
        candidate_id=candidate_id,
        pattern_id=pattern_id,
        topology_signature=topology_signature,
        extractor=extractor,
        extensions=extensions,
        occupied_cells=occupied_cells,
        output_stub=output_stub,
        output_dir=output_dir,
        transport_kind=transport_kind,
        base_throughput=base_throughput,
        base_score=base_score,
        route_probe_result=route_probe_result,
    )
