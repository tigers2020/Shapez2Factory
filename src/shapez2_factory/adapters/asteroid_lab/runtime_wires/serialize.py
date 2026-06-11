"""Serialize solver layer DTOs into runtime wire JSON."""

from __future__ import annotations

from typing import Any

from shapez2_factory.adapters.asteroid_lab.runtime_wires.envelope import (
    COMPLETE_MAP_MANIFEST_PATH_KEY,
    L3_WIRE_VERSION,
    L4_WIRE_VERSION,
    RUNTIME_WIRE_KIND,
    RUNTIME_WIRES_SCHEMA_VERSION,
    LayerOutcome,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    InnerPlacement,
    Layer04InnerFillResult,
    RouteableInnerGroupPlacement,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    CommittedRoute,
    Layer05Failure,
    Layer05Metrics,
    Layer05RoutePlan,
    ProjectedTransportTile,
    RouteGroupSummary,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    IntegratedRimGreedyResult,
    RimGreedyMetrics,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

_PROJECTION_CONTRACT: dict[str, list[str]] = {
    "allowed_uses": ["replay_projection_only"],
    "forbidden_uses": [
        "algorithm_input",
        "placement_decision",
        "routing_decision",
        "validation_repair",
        "solver_resume",
        "optimization_input",
    ],
}


def _coord_to_dict(coord: Coord) -> dict[str, int]:
    return {"x": coord[0], "y": coord[1]}


def _coords_to_list(coords: frozenset[Coord] | tuple[Coord, ...]) -> list[dict[str, int]]:
    return [_coord_to_dict(coord) for coord in sorted(coords)]


def _layer_envelope(
    *,
    layer_slug: str,
    outcome: LayerOutcome,
    skip_reason: str | None = None,
    failure_reason: str | None = None,
    body: dict[str, Any],
) -> dict[str, Any]:
    return {
        "layer_slug": layer_slug,
        "outcome": outcome.value,
        "skip_reason": skip_reason,
        "failure_reason": failure_reason,
        **body,
    }


def _serialize_rim_greedy_metrics(metrics: RimGreedyMetrics) -> dict[str, Any]:
    return {
        "rim_anchor_count": metrics.rim_anchor_count,
        "route_feasible_rim_anchor_count": metrics.route_feasible_rim_anchor_count,
        "committed_placement_count": metrics.committed_placement_count,
        "rejected_attempt_count": metrics.rejected_attempt_count,
        "reserved_route_cell_count": metrics.reserved_route_cell_count,
        "winning_variant_id": metrics.winning_variant_id,
        "pass2_score": metrics.pass2_score,
        "layer_skip_reason": metrics.layer_skip_reason,
        "canonical_layer_slug": metrics.canonical_layer_slug,
    }


def _serialize_committed_placement(
    placement: CommittedRimSeedPlacement,
    *,
    commit_index: int,
) -> dict[str, Any]:
    return {
        "commit_index": commit_index,
        "placement_id": placement.placement_id,
        "variant_id": placement.variant_id,
        "anchor": _coord_to_dict(placement.anchor),
        "output_dir": placement.output_dir,
        "seed_id": placement.seed_id,
        "miner_cells": _coords_to_list(placement.miner_cells),
        "extension_cells": _coords_to_list(placement.extension_cells),
        "m_output_stub": _coord_to_dict(placement.m_output_stub),
        "throughput_factor": placement.throughput_factor,
        "projection_hints": {
            "route_probe_path": _coords_to_list(placement.route_probe_path),
        },
    }


def _occupied_coords_from_placements(
    placements: tuple[InnerPlacement, ...],
) -> frozenset[Coord]:
    return frozenset(placement.coord for placement in placements)


def _serialize_inner_placement(placement: InnerPlacement) -> dict[str, Any]:
    return {
        "coord": _coord_to_dict(placement.coord),
        "pattern_id": placement.pattern_id,
        "rotation": placement.rotation,
    }


def _serialize_routeable_inner_group(
    group: RouteableInnerGroupPlacement,
) -> dict[str, Any]:
    return {
        "placement_id": group.placement_id,
        "anchor": _coord_to_dict(group.anchor),
        "miner_cells": _coords_to_list(group.miner_cells),
        "extension_cells": _coords_to_list(group.extension_cells),
        "m_output_stub": _coord_to_dict(group.m_output_stub),
        "throughput_factor": group.throughput_factor,
    }


def _serialize_layer04_metrics(result: Layer04InnerFillResult) -> dict[str, Any]:
    metrics = result.metrics
    if metrics is None:
        return {}
    return {
        "interior_occupied_cell_count": metrics.interior_occupied_cell_count,
        "coverage_ratio": metrics.coverage_ratio,
        "corridor_risk": metrics.corridor_risk,
        "fragment_penalty": metrics.fragment_penalty,
        "budget_interrupted": metrics.budget_interrupted,
    }


def _serialize_projected_transport_tile(tile: ProjectedTransportTile) -> dict[str, Any]:
    return {
        "coord": _coord_to_dict(tile.coord),
        "transport_kind": tile.transport_kind,
        "tile_id": tile.tile_id,
        "rotation": tile.rotation,
        "input_dirs": list(tile.input_dirs),
        "output_dirs": list(tile.output_dirs),
        "group_id": tile.group_id,
        "source_route_ids": list(tile.source_route_ids),
    }


def _serialize_committed_route(route: CommittedRoute) -> dict[str, Any]:
    return {
        "route_id": route.route_id,
        "placement_id": route.placement_id,
        "path_coords": _coords_to_list(route.path_coords),
        "group_id": route.group_id,
        "route_cost": route.route_cost,
    }


def _serialize_route_group(group: RouteGroupSummary) -> dict[str, Any]:
    return {
        "group_id": group.group_id,
        "transport_kind": group.transport_kind,
        "connector_ids": sorted(group.connector_ids),
        "member_placement_ids": sorted(group.member_placement_ids),
        "route_cells": _coords_to_list(group.route_cells),
        "used_m": group.used_m,
        "capacity_m": group.capacity_m,
    }


def _serialize_layer05_failure(failure: Layer05Failure) -> dict[str, Any]:
    return {
        "placement_id": failure.placement_id,
        "reason": failure.reason.value,
        "detail": failure.detail,
    }


def _serialize_layer05_metrics(metrics: Layer05Metrics) -> dict[str, Any]:
    return {
        "source_count": metrics.source_count,
        "routed_source_count": metrics.routed_source_count,
        "failed_source_count": metrics.failed_source_count,
        "total_route_cells": metrics.total_route_cells,
        "total_route_cost": metrics.total_route_cost,
    }


def _serialize_route_plan(plan: Layer05RoutePlan) -> dict[str, Any]:
    return {
        "version": plan.version,
        "resource_kind": plan.resource_kind,
        "transport_kind": plan.transport_kind,
        "routes": [_serialize_committed_route(route) for route in plan.routes],
        "groups": [_serialize_route_group(group) for group in plan.groups],
        "transport_tiles": [
            _serialize_projected_transport_tile(tile) for tile in plan.transport_tiles
        ],
        "failures": [_serialize_layer05_failure(failure) for failure in plan.failures],
        "metrics": _serialize_layer05_metrics(plan.metrics),
    }


def serialize_layer02_wire(
    plan: ExteriorConnectionPlan,
    *,
    outcome: LayerOutcome = LayerOutcome.COMPLETED,
    skip_reason: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    metrics = exterior_connector_plan_to_metrics_dict(plan)
    return _layer_envelope(
        layer_slug=LAYER_02_EXTERIOR_TRANSPORT,
        outcome=outcome,
        skip_reason=skip_reason,
        failure_reason=failure_reason,
        body={"exterior_connector_plan": metrics["exterior_connector_plan"]},
    )


def serialize_layer03_wire(
    result: IntegratedRimGreedyResult,
    *,
    outcome: LayerOutcome = LayerOutcome.COMPLETED,
    skip_reason: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    return _layer_envelope(
        layer_slug=LAYER_03_RIM_GREEDY_PLACEMENT,
        outcome=outcome,
        skip_reason=skip_reason,
        failure_reason=failure_reason,
        body={
            "wire_version": L3_WIRE_VERSION,
            "winning_variant_id": result.winning_variant_id,
            "metrics": _serialize_rim_greedy_metrics(result.metrics),
            "committed_placements": [
                _serialize_committed_placement(placement, commit_index=index)
                for index, placement in enumerate(result.committed_placements)
            ],
        },
    )


def serialize_layer04_wire(
    result: Layer04InnerFillResult,
    *,
    outcome: LayerOutcome = LayerOutcome.COMPLETED,
    skip_reason: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    occupied = _occupied_coords_from_placements(result.placements)
    return _layer_envelope(
        layer_slug=LAYER_04_INNER_PATTERN_FILL,
        outcome=outcome,
        skip_reason=skip_reason,
        failure_reason=failure_reason,
        body={
            "wire_version": L4_WIRE_VERSION,
            "placements": [_serialize_inner_placement(p) for p in result.placements],
            "interior_occupied_cells": _coords_to_list(occupied),
            "routeable_inner_groups": [
                _serialize_routeable_inner_group(group) for group in result.routeable_inner_groups
            ],
            "metrics": _serialize_layer04_metrics(result),
        },
    )


def serialize_layer05_wire(
    plan: Layer05RoutePlan,
    *,
    outcome: LayerOutcome = LayerOutcome.COMPLETED,
    skip_reason: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    return _layer_envelope(
        layer_slug=LAYER_05_TRANSPORT_ROUTING,
        outcome=outcome,
        skip_reason=skip_reason,
        failure_reason=failure_reason,
        body={"route_plan": _serialize_route_plan(plan)},
    )


def build_runtime_wires_document(
    *,
    run_key: str,
    complete_map_hash: str,
    transport_summary: dict[str, str],
    exterior_plan: ExteriorConnectionPlan | None = None,
    rim_greedy: IntegratedRimGreedyResult | None = None,
    inner_fill: Layer04InnerFillResult | None = None,
    route_plan: Layer05RoutePlan | None = None,
    core_build_id: str = "",
    written_at_utc: str = "",
) -> dict[str, Any]:
    layers: dict[str, Any] = {}
    if exterior_plan is not None:
        layers[LAYER_02_EXTERIOR_TRANSPORT] = serialize_layer02_wire(exterior_plan)
    if rim_greedy is not None:
        layers[LAYER_03_RIM_GREEDY_PLACEMENT] = serialize_layer03_wire(rim_greedy)
    if inner_fill is not None:
        layers[LAYER_04_INNER_PATTERN_FILL] = serialize_layer04_wire(inner_fill)
    if route_plan is not None:
        layers[LAYER_05_TRANSPORT_ROUTING] = serialize_layer05_wire(route_plan)

    return {
        "schema_version": RUNTIME_WIRES_SCHEMA_VERSION,
        "wire_kind": RUNTIME_WIRE_KIND,
        "core_build_id": core_build_id,
        "run_key": run_key,
        "written_at_utc": written_at_utc,
        "transport_summary": dict(transport_summary),
        "complete_map_ref": {
            "manifest_path_key": COMPLETE_MAP_MANIFEST_PATH_KEY,
            "content_hash": complete_map_hash,
        },
        "layers": layers,
        "projection_contract": dict(_PROJECTION_CONTRACT),
    }


__all__ = [
    "build_runtime_wires_document",
    "serialize_layer02_wire",
    "serialize_layer03_wire",
    "serialize_layer04_wire",
    "serialize_layer05_wire",
]
