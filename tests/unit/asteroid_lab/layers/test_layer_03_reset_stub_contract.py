"""Layer 03 reset stub — deterministic empty result (spec 2026-05-31)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    RimGreedyObservationPhase,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    ALGORITHM_STUB_ID,
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.layers.observability.post_summary_metrics import (
    build_layer03_rim_greedy_post_summary_metrics,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)

_RESET = Layer03SkipReason.ALGORITHM_RESET


def test_layer_03_returns_empty_result_without_algorithm() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.committed_placements == ()
    assert result.metrics.committed_placement_count == 0
    assert result.metrics.layer_skip_reason == _RESET
    assert result.metrics.layer_skip_reason == _RESET.value
    assert result.pass2_report.hard_fail is True
    phases = {e.phase for e in result.observability_events}
    assert RimGreedyObservationPhase.RIM_GREEDY_BEGIN in phases
    assert RimGreedyObservationPhase.RIM_GREEDY_COMPLETE in phases
    summary = build_layer03_rim_greedy_post_summary_metrics(result)
    assert summary["algorithm_stub"] == ALGORITHM_STUB_ID
    assert summary["layer_skip_reason"] == _RESET.value


def test_layer_03_missing_exterior_plan_uses_enum_skip_not_reset() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=None,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN
