"""Deserialize runtime wire JSON into projection DTOs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from shapez2_factory.adapters.asteroid_lab.runtime_wires.envelope import (
    DIAGNOSTIC_L3_ORDER_INVALID,
    DIAGNOSTIC_L4_PLACEMENT_MISMATCH,
    DIAGNOSTIC_SCHEMA_UNKNOWN,
    L3_WIRE_VERSION,
    L4_WIRE_VERSION,
    RUNTIME_WIRES_SCHEMA_VERSION,
    RuntimeWireValidationError,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    InnerPlacement,
    Layer04FillMetrics,
    Layer04InnerFillResult,
    Layer04SkipReason,
    RouteableInnerGroupPlacement,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    CommittedRoute,
    Layer05Failure,
    Layer05FailureReason,
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
    RimGreedyPass2Report,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


@dataclass(frozen=True, slots=True)
class RuntimeWiresProjectionBundle:
    exterior_plan_wire: dict[str, Any] | None
    rim_greedy: IntegratedRimGreedyResult | None
    inner_fill: Layer04InnerFillResult | None
    route_plan: Layer05RoutePlan | None


def _coord_from_dict(data: dict[str, Any]) -> Coord:
    return (int(data["x"]), int(data["y"]))


def _coords_from_list(items: list[dict[str, Any]]) -> frozenset[Coord]:
    return frozenset(_coord_from_dict(item) for item in items)


def _coords_tuple_from_list(items: list[dict[str, Any]]) -> tuple[Coord, ...]:
    return tuple(_coord_from_dict(item) for item in items)


def _require_dict(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        msg = f"{field} must be a dict"
        raise RuntimeWireValidationError("runtime_wire_invalid_shape", msg)
    return value


def _deserialize_rim_greedy_metrics(data: dict[str, Any]) -> RimGreedyMetrics:
    return RimGreedyMetrics(
        rim_anchor_count=int(data.get("rim_anchor_count", 0)),
        route_feasible_rim_anchor_count=int(data.get("route_feasible_rim_anchor_count", 0)),
        committed_placement_count=int(data.get("committed_placement_count", 0)),
        rejected_attempt_count=int(data.get("rejected_attempt_count", 0)),
        reserved_route_cell_count=int(data.get("reserved_route_cell_count", 0)),
        winning_variant_id=str(data.get("winning_variant_id", "")),
        pass2_score=data.get("pass2_score"),
        layer_skip_reason=data.get("layer_skip_reason"),
        canonical_layer_slug=str(
            data.get("canonical_layer_slug", LAYER_03_RIM_GREEDY_PLACEMENT),
        ),
    )


def _deserialize_committed_placement(item: dict[str, Any]) -> CommittedRimSeedPlacement:
    hints = _require_dict(item.get("projection_hints", {}), field="projection_hints")
    route_probe_path = _coords_tuple_from_list(
        list(hints.get("route_probe_path", [])),
    )
    return CommittedRimSeedPlacement(
        placement_id=str(item["placement_id"]),
        variant_id=str(item["variant_id"]),
        anchor=_coord_from_dict(_require_dict(item["anchor"], field="anchor")),
        output_dir=str(item["output_dir"]),
        seed_id=str(item["seed_id"]),
        miner_cells=_coords_from_list(list(item.get("miner_cells", []))),
        extension_cells=_coords_from_list(list(item.get("extension_cells", []))),
        m_output_stub=_coord_from_dict(_require_dict(item["m_output_stub"], field="m_output_stub")),
        throughput_factor=int(item["throughput_factor"]),
        route_probe_path=route_probe_path,
    )


def _validate_l3_commit_index_order(wire: dict[str, Any]) -> None:
    placements = wire.get("committed_placements", [])
    if not isinstance(placements, list):
        msg = "committed_placements must be a list"
        raise RuntimeWireValidationError(DIAGNOSTIC_L3_ORDER_INVALID, msg)
    for index, item in enumerate(placements):
        if not isinstance(item, dict):
            msg = "committed_placements entries must be dicts"
            raise RuntimeWireValidationError(DIAGNOSTIC_L3_ORDER_INVALID, msg)
        commit_index = item.get("commit_index")
        if commit_index != index:
            msg = (
                f"committed_placements[{index}] commit_index={commit_index!r} "
                f"does not match array position"
            )
            raise RuntimeWireValidationError(DIAGNOSTIC_L3_ORDER_INVALID, msg)


def deserialize_l3_wire(wire: dict[str, Any]) -> IntegratedRimGreedyResult:
    _validate_l3_commit_index_order(wire)
    metrics = _deserialize_rim_greedy_metrics(
        _require_dict(wire.get("metrics", {}), field="metrics")
    )
    placements = tuple(
        _deserialize_committed_placement(_require_dict(item, field="committed_placement"))
        for item in wire.get("committed_placements", [])
    )
    winning_variant_id = str(wire.get("winning_variant_id", metrics.winning_variant_id))
    miner_count = sum(len(p.miner_cells) for p in placements)
    extension_count = sum(len(p.extension_cells) for p in placements)
    total_route_length = sum(len(p.route_probe_path) for p in placements)
    pass2_score = metrics.pass2_score
    occupied_equipment = frozenset(
        coord
        for placement in placements
        for coord in (*placement.miner_cells, *placement.extension_cells)
    )
    reserved_route = frozenset(
        coord for placement in placements for coord in placement.route_probe_path
    )
    base = build_empty_integrated_rim_greedy_result()
    return replace(
        base,
        committed_placements=placements,
        occupied_equipment_cells=occupied_equipment,
        reserved_route_cells=reserved_route,
        winning_variant_id=winning_variant_id,
        metrics=replace(
            metrics,
            committed_placement_count=len(placements),
            winning_variant_id=winning_variant_id,
        ),
        pass2_report=RimGreedyPass2Report(
            variant_id=winning_variant_id,
            score=pass2_score,
            hard_fail=not placements,
            miner_count=miner_count,
            extension_count=extension_count,
            total_route_length=total_route_length,
        ),
    )


def _deserialize_inner_placement(item: dict[str, Any]) -> InnerPlacement:
    return InnerPlacement(
        coord=_coord_from_dict(_require_dict(item["coord"], field="coord")),
        pattern_id=str(item["pattern_id"]),
        rotation=int(item.get("rotation", 0)),
    )


def _deserialize_routeable_inner_group(item: dict[str, Any]) -> RouteableInnerGroupPlacement:
    return RouteableInnerGroupPlacement(
        placement_id=str(item["placement_id"]),
        anchor=_coord_from_dict(_require_dict(item["anchor"], field="anchor")),
        miner_cells=_coords_from_list(list(item.get("miner_cells", []))),
        extension_cells=_coords_from_list(list(item.get("extension_cells", []))),
        m_output_stub=_coord_from_dict(_require_dict(item["m_output_stub"], field="m_output_stub")),
        throughput_factor=int(item["throughput_factor"]),
    )


def _occupied_from_placements(placements: tuple[InnerPlacement, ...]) -> frozenset[Coord]:
    return frozenset(placement.coord for placement in placements)


def _validate_l4_placements_consistency(
    *,
    placements: tuple[InnerPlacement, ...],
    interior_occupied_cells: frozenset[Coord],
) -> None:
    derived = _occupied_from_placements(placements)
    if derived != interior_occupied_cells:
        msg = "interior_occupied_cells does not match placements coord set"
        raise RuntimeWireValidationError(DIAGNOSTIC_L4_PLACEMENT_MISMATCH, msg)


def _deserialize_layer04_metrics(data: dict[str, Any]) -> Layer04FillMetrics | None:
    if not data:
        return None
    return Layer04FillMetrics(
        interior_occupied_cell_count=int(data.get("interior_occupied_cell_count", 0)),
        coverage_ratio=float(data.get("coverage_ratio", 0.0)),
        corridor_risk=float(data.get("corridor_risk", 0.0)),
        fragment_penalty=float(data.get("fragment_penalty", 0.0)),
        budget_interrupted=bool(data.get("budget_interrupted", False)),
    )


def deserialize_l4_wire(wire: dict[str, Any]) -> Layer04InnerFillResult:
    placements = tuple(
        _deserialize_inner_placement(_require_dict(item, field="placement"))
        for item in wire.get("placements", [])
    )
    interior_occupied_cells = _coords_from_list(
        list(wire.get("interior_occupied_cells", [])),
    )
    _validate_l4_placements_consistency(
        placements=placements,
        interior_occupied_cells=interior_occupied_cells,
    )
    skip_reason_raw = wire.get("skip_reason")
    skip_reason = Layer04SkipReason(skip_reason_raw) if skip_reason_raw else None
    return Layer04InnerFillResult(
        interior_occupied_cells=interior_occupied_cells,
        placements=placements,
        routeable_inner_groups=tuple(
            _deserialize_routeable_inner_group(_require_dict(item, field="routeable_inner_group"))
            for item in wire.get("routeable_inner_groups", [])
        ),
        metrics=_deserialize_layer04_metrics(
            _require_dict(wire.get("metrics", {}), field="metrics")
        ),
        skip_reason=skip_reason,
    )


def _deserialize_projected_transport_tile(item: dict[str, Any]) -> ProjectedTransportTile:
    return ProjectedTransportTile(
        coord=_coord_from_dict(_require_dict(item["coord"], field="coord")),
        transport_kind=str(item["transport_kind"]),
        tile_id=str(item["tile_id"]),
        rotation=int(item["rotation"]),
        input_dirs=tuple(str(v) for v in item.get("input_dirs", ())),
        output_dirs=tuple(str(v) for v in item.get("output_dirs", ())),
        group_id=str(item["group_id"]),
        source_route_ids=tuple(str(v) for v in item.get("source_route_ids", ())),
    )


def _deserialize_committed_route(item: dict[str, Any]) -> CommittedRoute:
    return CommittedRoute(
        route_id=str(item["route_id"]),
        placement_id=str(item["placement_id"]),
        path_coords=_coords_tuple_from_list(list(item.get("path_coords", []))),
        group_id=str(item["group_id"]),
        route_cost=int(item["route_cost"]),
    )


def _deserialize_route_group(item: dict[str, Any]) -> RouteGroupSummary:
    return RouteGroupSummary(
        group_id=str(item["group_id"]),
        transport_kind=str(item["transport_kind"]),
        connector_ids=frozenset(str(v) for v in item.get("connector_ids", ())),
        member_placement_ids=frozenset(str(v) for v in item.get("member_placement_ids", ())),
        route_cells=_coords_from_list(list(item.get("route_cells", []))),
        used_m=int(item["used_m"]),
        capacity_m=int(item["capacity_m"]),
    )


def _deserialize_layer05_failure(item: dict[str, Any]) -> Layer05Failure:
    return Layer05Failure(
        placement_id=item.get("placement_id"),
        reason=Layer05FailureReason(str(item["reason"])),
        detail=str(item.get("detail", "")),
    )


def _deserialize_layer05_metrics(data: dict[str, Any]) -> Layer05Metrics:
    return Layer05Metrics(
        source_count=int(data.get("source_count", 0)),
        routed_source_count=int(data.get("routed_source_count", 0)),
        failed_source_count=int(data.get("failed_source_count", 0)),
        total_route_cells=int(data.get("total_route_cells", 0)),
        total_route_cost=int(data.get("total_route_cost", 0)),
    )


def deserialize_l5_wire(wire: dict[str, Any]) -> Layer05RoutePlan:
    route_plan = _require_dict(wire.get("route_plan", {}), field="route_plan")
    return Layer05RoutePlan(
        version=str(route_plan["version"]),
        resource_kind=str(route_plan["resource_kind"]),
        transport_kind=str(route_plan["transport_kind"]),
        routes=tuple(
            _deserialize_committed_route(_require_dict(item, field="route"))
            for item in route_plan.get("routes", [])
        ),
        groups=tuple(
            _deserialize_route_group(_require_dict(item, field="group"))
            for item in route_plan.get("groups", [])
        ),
        transport_tiles=tuple(
            _deserialize_projected_transport_tile(_require_dict(item, field="transport_tile"))
            for item in route_plan.get("transport_tiles", [])
        ),
        failures=tuple(
            _deserialize_layer05_failure(_require_dict(item, field="failure"))
            for item in route_plan.get("failures", [])
        ),
        metrics=_deserialize_layer05_metrics(
            _require_dict(route_plan.get("metrics", {}), field="metrics"),
        ),
    )


def _validate_schema_version(document: dict[str, Any]) -> None:
    schema_version = document.get("schema_version")
    if schema_version != RUNTIME_WIRES_SCHEMA_VERSION:
        msg = f"unsupported runtime wire schema_version={schema_version!r}"
        raise RuntimeWireValidationError(DIAGNOSTIC_SCHEMA_UNKNOWN, msg)


def deserialize_runtime_wires_document(document: dict[str, Any]) -> RuntimeWiresProjectionBundle:
    _validate_schema_version(document)
    layers = _require_dict(document.get("layers", {}), field="layers")

    exterior_plan_wire: dict[str, Any] | None = None
    l2 = layers.get(LAYER_02_EXTERIOR_TRANSPORT)
    if isinstance(l2, dict):
        plan = l2.get("exterior_connector_plan")
        if isinstance(plan, dict):
            exterior_plan_wire = plan

    rim_greedy: IntegratedRimGreedyResult | None = None
    l3 = layers.get(LAYER_03_RIM_GREEDY_PLACEMENT)
    if isinstance(l3, dict):
        if l3.get("wire_version", L3_WIRE_VERSION) != L3_WIRE_VERSION:
            msg = f"unsupported L3 wire_version={l3.get('wire_version')!r}"
            raise RuntimeWireValidationError(DIAGNOSTIC_SCHEMA_UNKNOWN, msg)
        rim_greedy = deserialize_l3_wire(l3)

    inner_fill: Layer04InnerFillResult | None = None
    l4 = layers.get(LAYER_04_INNER_PATTERN_FILL)
    if isinstance(l4, dict):
        if l4.get("wire_version", L4_WIRE_VERSION) != L4_WIRE_VERSION:
            msg = f"unsupported L4 wire_version={l4.get('wire_version')!r}"
            raise RuntimeWireValidationError(DIAGNOSTIC_SCHEMA_UNKNOWN, msg)
        inner_fill = deserialize_l4_wire(l4)

    route_plan: Layer05RoutePlan | None = None
    l5 = layers.get(LAYER_05_TRANSPORT_ROUTING)
    if isinstance(l5, dict):
        route_plan = deserialize_l5_wire(l5)

    return RuntimeWiresProjectionBundle(
        exterior_plan_wire=exterior_plan_wire,
        rim_greedy=rim_greedy,
        inner_fill=inner_fill,
        route_plan=route_plan,
    )


__all__ = [
    "RuntimeWiresProjectionBundle",
    "deserialize_l3_wire",
    "deserialize_l4_wire",
    "deserialize_l5_wire",
    "deserialize_runtime_wires_document",
]
