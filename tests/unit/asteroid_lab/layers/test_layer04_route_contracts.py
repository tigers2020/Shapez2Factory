"""Layer 04 route plan contract tests (PR-L4-0)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
    Layer04RoutePlan,
    Layer04SourceView,
)


def test_layer04_failure_reason_route_not_found() -> None:
    assert Layer04FailureReason.ROUTE_NOT_FOUND.value == "route_not_found"


def test_layer05_failure_reason_interior_occupied_blocked() -> None:
    from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
        Layer05FailureReason,
    )

    assert Layer05FailureReason.INTERIOR_OCCUPIED_BLOCKED.value == "interior_occupied_blocked"


def test_layer04_source_view_frozen() -> None:
    view = Layer04SourceView(
        placement_id="p1",
        m_output_stub=(1, 0),
        source_load_m=12,
        throughput_factor=12,
        equipment_cells=frozenset(),
        route_probe_path=(),
    )
    assert view.source_load_m == 12
    assert view.throughput_factor == 12


def test_layer04_route_plan_empty() -> None:
    plan = Layer04RoutePlan.empty(resource_kind="shape", transport_kind="space_belt")
    assert plan.transport_tiles == ()
    assert plan.failures == ()
    assert plan.routes == ()
    assert plan.groups == ()
    assert plan.resource_kind == "shape"
    assert plan.transport_kind == "space_belt"


def test_layer04_route_plan_is_layer05_alias() -> None:
    from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
        Layer05RoutePlan,
    )

    assert Layer04RoutePlan is Layer05RoutePlan
