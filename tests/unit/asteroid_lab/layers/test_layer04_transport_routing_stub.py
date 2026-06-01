"""Layer 04 transport routing stub entrypoint (PR-L4-0)."""

from __future__ import annotations

import warnings

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
    Layer04RoutePlan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    run_layer_04_rim_bundle_placement,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.run import (
    run_layer_04_transport_routing,
)


def test_layer04_transport_routing_stub_returns_empty_plan() -> None:
    plan = run_layer_04_transport_routing(
        complete_map=None,
        exterior_plan=object(),  # type: ignore[arg-type]
        rim_result=None,
        resource_kind="shape",
        budget_ctx=None,
    )
    assert isinstance(plan, Layer04RoutePlan)
    assert plan.transport_kind == "space_belt"
    assert plan.routes == ()


def test_layer04_transport_routing_missing_exterior_plan_failure() -> None:
    plan = run_layer_04_transport_routing(exterior_plan=None)
    assert len(plan.failures) == 1
    assert plan.failures[0].reason is Layer04FailureReason.MISSING_L2_EXTERIOR_PLAN


def test_layer04_rim_bundle_shim_still_disabled_with_deprecation() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        result = run_layer_04_rim_bundle_placement()
    assert result.status == "DISABLED"
    assert any("layer_04_transport_routing" in str(w.message) for w in caught)
