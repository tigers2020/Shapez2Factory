"""Runtime wire serde round-trip and validation guards."""

from __future__ import annotations

from dataclasses import replace

import pytest

from shapez2_factory.adapters.asteroid_lab.runtime_wires.deserialize import (
    deserialize_l3_wire,
    deserialize_l4_wire,
    deserialize_runtime_wires_document,
)
from shapez2_factory.adapters.asteroid_lab.runtime_wires.envelope import (
    RUNTIME_WIRES_SCHEMA_VERSION,
    LayerOutcome,
    RuntimeWireValidationError,
)
from shapez2_factory.adapters.asteroid_lab.runtime_wires.serialize import (
    build_runtime_wires_document,
    serialize_layer02_wire,
    serialize_layer03_wire,
    serialize_layer04_wire,
    serialize_layer05_wire,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    InnerPlacement,
    Layer04FillMetrics,
    Layer04InnerFillResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    LAYER05_ROUTE_PLAN_VERSION,
    Layer05Metrics,
    Layer05RoutePlan,
    ProjectedTransportTile,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    RimGreedyMetrics,
    build_empty_integrated_rim_greedy_result,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    minimal_l2_plan_for_golden,
)


def test_runtime_wire_schema_version() -> None:
    assert RUNTIME_WIRES_SCHEMA_VERSION == "solver_runtime_wires_v1"


def test_layer_outcome_values() -> None:
    assert set(LayerOutcome) == {
        LayerOutcome.COMPLETED,
        LayerOutcome.PARTIAL_BUDGET,
        LayerOutcome.SKIPPED,
        LayerOutcome.FAILED,
    }


def _minimal_l3_result() -> object:
    placement = CommittedRimSeedPlacement(
        placement_id="p-001",
        variant_id="m0e",
        anchor=(1, 2),
        output_dir="E",
        seed_id="m0e",
        miner_cells=frozenset({(1, 2)}),
        extension_cells=frozenset({(2, 2)}),
        m_output_stub=(3, 2),
        throughput_factor=4,
        route_probe_path=((4, 2),),
    )
    return replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
        winning_variant_id="m0e",
        metrics=RimGreedyMetrics(
            rim_anchor_count=4,
            route_feasible_rim_anchor_count=4,
            committed_placement_count=1,
            winning_variant_id="m0e",
            pass2_score=4.0,
        ),
    )


def _minimal_l4_result() -> Layer04InnerFillResult:
    return Layer04InnerFillResult(
        interior_occupied_cells=frozenset({(3, 3)}),
        placements=(
            InnerPlacement(
                coord=(3, 3),
                pattern_id="builtin_1x1_field_block",
                rotation=0,
            ),
        ),
        metrics=Layer04FillMetrics(
            interior_occupied_cell_count=1,
            coverage_ratio=0.1,
        ),
    )


def _minimal_l5_plan() -> Layer05RoutePlan:
    tile = ProjectedTransportTile(
        coord=(6, 4),
        transport_kind="shape_belt",
        tile_id="ShapeBelt_Forward",
        rotation=0,
        input_dirs=("W",),
        output_dirs=("E",),
        group_id="conn_ext",
        source_route_ids=("route_p0",),
    )
    return Layer05RoutePlan(
        version=LAYER05_ROUTE_PLAN_VERSION,
        resource_kind="shape",
        transport_kind="shape_belt",
        routes=(),
        groups=(),
        transport_tiles=(tile,),
        failures=(),
        metrics=Layer05Metrics(source_count=1, routed_source_count=1),
    )


def test_l2_wire_serializes_exterior_connector_plan_v2() -> None:
    wire = serialize_layer02_wire(minimal_l2_plan_for_golden())
    assert wire["exterior_connector_plan"]["version"] == "exterior_connector_plan.v2"


def test_l3_wire_commit_index_order_enforced_on_deserialize() -> None:
    wire = {
        "layer_slug": "layer_03_rim_greedy_placement",
        "outcome": "completed",
        "wire_version": "integrated_rim_greedy_result_v1",
        "winning_variant_id": "m0e",
        "metrics": {},
        "committed_placements": [
            {
                "commit_index": 1,
                "placement_id": "b",
                "variant_id": "m0e",
                "anchor": {"x": 1, "y": 2},
                "output_dir": "E",
                "seed_id": "m0e",
                "miner_cells": [{"x": 1, "y": 2}],
                "extension_cells": [],
                "m_output_stub": {"x": 3, "y": 2},
                "throughput_factor": 4,
                "projection_hints": {"route_probe_path": []},
            },
            {
                "commit_index": 0,
                "placement_id": "a",
                "variant_id": "m0e",
                "anchor": {"x": 2, "y": 2},
                "output_dir": "E",
                "seed_id": "m0e",
                "miner_cells": [{"x": 2, "y": 2}],
                "extension_cells": [],
                "m_output_stub": {"x": 4, "y": 2},
                "throughput_factor": 4,
                "projection_hints": {"route_probe_path": []},
            },
        ],
    }
    with pytest.raises(RuntimeWireValidationError) as exc:
        deserialize_l3_wire(wire)
    assert exc.value.code == "runtime_wire_l3_order_invalid"


def test_l4_wire_rejects_placements_occupied_mismatch() -> None:
    wire = {
        "layer_slug": "layer_04_inner_pattern_fill",
        "outcome": "completed",
        "wire_version": "layer04_inner_fill_result_v1",
        "placements": [
            {
                "coord": {"x": 1, "y": 1},
                "pattern_id": "builtin_1x1_field_block",
                "rotation": 0,
            }
        ],
        "interior_occupied_cells": [{"x": 2, "y": 2}],
        "routeable_inner_groups": [],
        "metrics": {},
    }
    with pytest.raises(RuntimeWireValidationError) as exc:
        deserialize_l4_wire(wire)
    assert exc.value.code == "runtime_wire_l4_placement_mismatch"


def test_runtime_wires_document_includes_projection_contract() -> None:
    doc = build_runtime_wires_document(
        run_key="rk-test",
        core_build_id="build-1",
        written_at_utc="2026-06-10T00:00:00Z",
        complete_map_hash="abc123",
        transport_summary={
            "requested_resource_kind": "shape",
            "effective_transport_kind": "shape_belt",
        },
        exterior_plan=minimal_l2_plan_for_golden(),
        rim_greedy=_minimal_l3_result(),
        inner_fill=_minimal_l4_result(),
        route_plan=_minimal_l5_plan(),
    )
    assert doc["schema_version"] == RUNTIME_WIRES_SCHEMA_VERSION
    assert doc["projection_contract"]["allowed_uses"] == ["replay_projection_only"]
    assert "algorithm_input" in doc["projection_contract"]["forbidden_uses"]
    assert doc["complete_map_ref"] == {
        "manifest_path_key": "layer01_complete_map",
        "content_hash": "abc123",
    }
    assert doc["transport_summary"]["effective_transport_kind"] == "shape_belt"


def test_runtime_wires_round_trip_minimal_fixtures() -> None:
    l3 = _minimal_l3_result()
    l4 = _minimal_l4_result()
    l5 = _minimal_l5_plan()
    doc = build_runtime_wires_document(
        run_key="rk-roundtrip",
        written_at_utc="2026-06-10T00:00:00Z",
        complete_map_hash="hash-roundtrip",
        transport_summary={
            "requested_resource_kind": "shape",
            "effective_transport_kind": "shape_belt",
        },
        exterior_plan=minimal_l2_plan_for_golden(),
        rim_greedy=l3,
        inner_fill=l4,
        route_plan=l5,
    )

    bundle = deserialize_runtime_wires_document(doc)

    assert bundle.exterior_plan_wire is not None
    assert bundle.exterior_plan_wire["version"] == "exterior_connector_plan.v2"

    assert bundle.rim_greedy is not None
    assert len(bundle.rim_greedy.committed_placements) == 1
    placement = bundle.rim_greedy.committed_placements[0]
    assert placement.placement_id == "p-001"
    assert placement.route_probe_path == ((4, 2),)

    assert bundle.inner_fill is not None
    assert bundle.inner_fill.placements[0].coord == (3, 3)

    assert bundle.route_plan is not None
    assert bundle.route_plan.version == LAYER05_ROUTE_PLAN_VERSION
    assert len(bundle.route_plan.transport_tiles) == 1
    assert bundle.route_plan.transport_tiles[0].coord == (6, 4)


def test_l3_serialize_preserves_commit_index_and_projection_hints() -> None:
    wire = serialize_layer03_wire(_minimal_l3_result())
    placements = wire["committed_placements"]
    assert placements[0]["commit_index"] == 0
    assert placements[0]["projection_hints"]["route_probe_path"] == [{"x": 4, "y": 2}]


def test_l4_serialize_derives_interior_occupied_cells_from_placements() -> None:
    wire = serialize_layer04_wire(_minimal_l4_result())
    assert wire["interior_occupied_cells"] == [{"x": 3, "y": 3}]


def test_l5_serialize_wraps_route_plan_version() -> None:
    wire = serialize_layer05_wire(_minimal_l5_plan())
    assert wire["route_plan"]["version"] == LAYER05_ROUTE_PLAN_VERSION
