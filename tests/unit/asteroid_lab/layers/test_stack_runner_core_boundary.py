"""PR-CLI-2e Step 2 ??core/Django boundary for stack_runner.

The Django ``stack_runner`` is a thin wrapper that delegates orchestration to the pure core runner
and owns only the log-writing side effect; the layer-4 disabled result lives entirely in core.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django_apps.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
    LayerPostSummaryRecord,
)
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
)
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from django_apps.asteroid_lab.layers.stack_runner import run_layers_02_to_06
from shapez2_factory.application.asteroid_lab.stack_runner import CoreStackRunResult


def test_django_run_full_wrapper_delegates_to_core_runner() -> None:
    rec_a = LayerPostSummaryRecord(
        layer_slug=LAYER_02_EXTERIOR_TRANSPORT,
        layer_index=2,
        outcome=LayerPostSummaryOutcome.COMPLETED,
        elapsed_ms=1,
        remaining_budget_ms=100,
        metrics={"k": "a"},
    )
    rec_b = LayerPostSummaryRecord(
        layer_slug=LAYER_03_RIM_GREEDY_PLACEMENT,
        layer_index=3,
        outcome=LayerPostSummaryOutcome.COMPLETED,
        elapsed_ms=2,
        remaining_budget_ms=50,
        metrics={"k": "b"},
    )
    core_stack = StackRunResult(
        status=StackRunStatus.SUCCESS,
        completed_layer_slugs=(LAYER_02_EXTERIOR_TRANSPORT, LAYER_03_RIM_GREEDY_PLACEMENT),
        failed_layer_slug=None,
        diagnostic_snapshot=None,
    )
    core_result = CoreStackRunResult(stack_result=core_stack, layer_summaries=(rec_a, rec_b))

    session = MagicMock()
    sentinel_map = object()
    sentinel_ctx = object()
    sentinel_runners: tuple[object, ...] = ()

    with patch(
        "django_apps.asteroid_lab.layers.stack_runner._core_run_layers_02_to_06",
        return_value=core_result,
    ) as core_mock:
        result = run_layers_02_to_06(
            complete_map=sentinel_map,  # type: ignore[arg-type]
            budget_ctx=sentinel_ctx,  # type: ignore[arg-type]
            runners=sentinel_runners,  # type: ignore[arg-type]
            post_summary_session=session,
        )

    core_mock.assert_called_once_with(
        complete_map=sentinel_map,
        budget_ctx=sentinel_ctx,
        runners=sentinel_runners,
    )
    assert result is core_stack
    written = [call.args[0] for call in session.write_layer_post_summary.call_args_list]
    assert written == [rec_a, rec_b]


def test_layer4_disabled_result_is_core_pure() -> None:
    from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_disabled import (
        Layer04DisabledResult,
    )
    from shapez2_factory.application.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        empty_layer04_rim_placement_result,
    )

    placement = empty_layer04_rim_placement_result()
    assert len(placement.provisional_overlay.occupied_cells) == 0

    disabled = Layer04DisabledResult.superseded()
    assert disabled.status == "DISABLED"
    assert len(disabled.provisional_overlay.occupied_cells) == 0
