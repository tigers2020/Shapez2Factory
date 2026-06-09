"""Layer 05 failed-source diagnostics instrumentation tests."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_failed_source_diagnostics import (  # noqa: E501
    Layer05FailureBucket,
    aggregate_failure_histogram,
    failure_reason_to_bucket,
    format_l5_failure_eval_diagnostics,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    RimGreedyMetrics,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.failed_source_diagnostics import (  # noqa: E501
    build_failed_source_diagnostic,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.sequential_router import (  # noqa: E501
    route_layer04_sequential,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.source_adapter import (  # noqa: E501
    build_layer04_sources,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


def _exterior_plan(connector_void: tuple[int, int]) -> ExteriorConnectionPlan:
    conn = ExteriorConnector(
        connector_id="ext_conn_00",
        void_coord=connector_void,
        edge=CardinalEdge.WEST,
        layout_t="SpaceBelt_Forward",
        rotation=0,
        capacity_per_min=Decimal("5760"),
        coords=(connector_void,),
        role=ExteriorConnectorRole.REQUIRED,
    )
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5760"),
        per_connector_capacity_per_min=Decimal("5760"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(conn,),
        unmet_reason=None,
    )


def _placement(
    placement_id: str,
    stub: tuple[int, int],
    load_m: int,
) -> CommittedRimSeedPlacement:
    return CommittedRimSeedPlacement(
        placement_id=placement_id,
        variant_id="v1",
        anchor=(0, 0),
        output_dir="W",
        seed_id="gene_a",
        miner_cells=frozenset({(0, 0)}),
        extension_cells=frozenset(),
        m_output_stub=stub,
        throughput_factor=load_m,
        route_probe_path=((stub[0], stub[1]),),
    )


def test_failure_reason_to_bucket_mapping() -> None:
    assert (
        failure_reason_to_bucket(Layer04FailureReason.CAPACITY_OVERFLOW)
        == Layer05FailureBucket.ROUTE_BUDGET_EXHAUSTED
    )
    assert (
        failure_reason_to_bucket(
            Layer04FailureReason.ROUTE_NOT_FOUND,
            detail="blocked_by_l4_interior_count=3;blocked_by_equipment_count=1",
        )
        == Layer05FailureBucket.BLOCKED_BY_EQUIPMENT_OR_INTERIOR
    )


def test_build_failed_source_diagnostic_is_deterministic() -> None:
    rim = replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(_placement("p1", (-1, 1), 8),),
    )
    source = build_layer04_sources(rim)[0]
    first = build_failed_source_diagnostic(
        source=source,
        placement=rim.committed_placements[0],
        transport_kind="shape",
        reason=Layer04FailureReason.CAPACITY_OVERFLOW,
        detail="ext_conn_00",
        goals=(),
    )
    second = build_failed_source_diagnostic(
        source=source,
        placement=rim.committed_placements[0],
        transport_kind="shape",
        reason=Layer04FailureReason.CAPACITY_OVERFLOW,
        detail="ext_conn_00",
        goals=(),
    )
    assert first == second


def test_sequential_router_emits_failed_source_diagnostics() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    exterior = _exterior_plan((-1, 0))
    rim = replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(
            _placement("p1", (-1, 1), 8),
            _placement("p2", (-1, 2), 8),
        ),
        metrics=RimGreedyMetrics(committed_placement_count=2),
    )
    plan = route_layer04_sequential(
        complete_map=cm,
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
    )
    assert len(plan.routes) == 1
    assert len(plan.failures) == 1
    assert len(plan.failed_source_diagnostics) == 1
    entry = plan.failed_source_diagnostics[0]
    assert entry.source_id == "p2"
    assert entry.failure_bucket == Layer05FailureBucket.ROUTE_BUDGET_EXHAUSTED
    histogram = aggregate_failure_histogram(plan.failed_source_diagnostics)
    assert histogram[Layer05FailureBucket.ROUTE_BUDGET_EXHAUSTED.value] == 1


def test_format_l5_failure_eval_diagnostics_histogram() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    exterior = _exterior_plan((-1, 0))
    rim = replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(
            _placement("p1", (-1, 1), 8),
            _placement("p2", (-1, 2), 8),
        ),
        metrics=RimGreedyMetrics(committed_placement_count=2),
    )
    plan = route_layer04_sequential(
        complete_map=cm,
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
    )
    lines = format_l5_failure_eval_diagnostics(plan)
    assert any(line.startswith("l5_failure_bucket:") for line in lines)
    assert any(line.startswith("l5_failure_reason:") for line in lines)
    assert any(line.startswith("l5_failed_example:p2") for line in lines)
