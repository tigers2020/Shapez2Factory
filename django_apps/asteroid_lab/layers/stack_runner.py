"""Django wrapper over the pure core stack orchestrator (logs/settings/files live here)."""

from __future__ import annotations

import time

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_post_summary import LayerPostSummaryOutcome
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYER_06_COMMIT_VALIDATE,
)
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.layer_01_reconstruction.output import (
    Layer01ReconstructionOutput,
)
from django_apps.asteroid_lab.layers.layer_01_reconstruction.run import run_layer_01
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.run import (
    run_layer_02_exterior_transport,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.layers.layer_04_transport_routing.run import (
    run_layer_05_transport_routing,
)
from django_apps.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)
from django_apps.asteroid_lab.layers.layer_06_commit_validate.run import (
    run_layer_06_commit_validate,
)
from django_apps.asteroid_lab.layers.observability.layer_post_summary_log import (
    LayerPostSummaryLogSession,
    build_layer01_post_summary_metrics,
    create_layer_post_summary_log_session,
    emit_layer_post_summary,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.space_transport_catalog_loader import (
    try_load_default_space_transport_catalog,
)
from shapez2_factory.application.asteroid_lab.stack_runner import (
    _LAYER_INDEX,
    LAYER_STACK_BUDGET_MS,
    CoreStackRunResult,
    _Layer02To05Runner,
    _LayerStackRunner,
)
from shapez2_factory.application.asteroid_lab.stack_runner import (
    run_layers_02_to_06 as _core_run_layers_02_to_06,
)

_DEFAULT_RUNNERS: tuple[_LayerStackRunner, ...] = (
    _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, run_layer_02_exterior_transport),
    _LayerStackRunner(LAYER_03_RIM_GREEDY_PLACEMENT, run_layer_03_rim_greedy_placement),
    _LayerStackRunner(LAYER_04_INNER_PATTERN_FILL, run_layer_04_inner_pattern_fill),
    _LayerStackRunner(LAYER_05_TRANSPORT_ROUTING, run_layer_05_transport_routing),
    _LayerStackRunner(LAYER_06_COMMIT_VALIDATE, run_layer_06_commit_validate),
)


def run_layers_02_to_06(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_LayerStackRunner, ...] = _DEFAULT_RUNNERS,
    post_summary_session: LayerPostSummaryLogSession | None = None,
    capacity_envelope: dict[str, object] | None = None,
    throughput_target_percent: int | None = 80,
) -> StackRunResult:
    core_result: CoreStackRunResult = _core_run_layers_02_to_06(
        complete_map=complete_map,
        budget_ctx=budget_ctx,
        runners=runners,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=throughput_target_percent,
        transport_catalog=try_load_default_space_transport_catalog(),
    )
    if post_summary_session is not None:
        for record in core_result.layer_summaries:
            post_summary_session.write_layer_post_summary(record)
    return core_result.stack_result


def run_layers_02_to_05(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_LayerStackRunner, ...] = _DEFAULT_RUNNERS,
    post_summary_session: LayerPostSummaryLogSession | None = None,
) -> StackRunResult:
    """Deprecated alias for ``run_layers_02_to_06`` (PR-3c layer renumber)."""
    return run_layers_02_to_06(
        complete_map=complete_map,
        budget_ctx=budget_ctx,
        runners=runners,
        post_summary_session=post_summary_session,
    )


def run_full_from_cleanup_recon(
    *,
    cleanup: CleanupResult,
    recon: ReconstructionResult,
    budget_ctx: LayerBudgetContext | None = None,
    runners: tuple[_LayerStackRunner, ...] = _DEFAULT_RUNNERS,
    post_summary_session: LayerPostSummaryLogSession | None = None,
    project_slug: str | None = None,
    solver_run_id: int | None = None,
) -> tuple[Layer01ReconstructionOutput, StackRunResult]:
    session = post_summary_session
    owns_session = session is None
    if owns_session:
        session = create_layer_post_summary_log_session(
            project_slug=project_slug,
            solver_run_id=solver_run_id,
        )
    stack_result: StackRunResult | None = None
    try:
        l1_started = time.monotonic()
        layer01 = run_layer_01(cleanup=cleanup, recon=recon)
        l1_elapsed_ms = max(0, int((time.monotonic() - l1_started) * 1000))
        emit_layer_post_summary(
            session,
            layer_slug=LAYER_01_RECONSTRUCTION,
            layer_index=_LAYER_INDEX[LAYER_01_RECONSTRUCTION],
            outcome=LayerPostSummaryOutcome.COMPLETED,
            elapsed_ms=l1_elapsed_ms,
            remaining_budget_ms=None,
            metrics=build_layer01_post_summary_metrics(layer01),
        )
        ctx = budget_ctx or LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS)
        stack_result = run_layers_02_to_06(
            complete_map=layer01.complete_map,
            budget_ctx=ctx,
            runners=runners,
            post_summary_session=session,
            capacity_envelope=layer01.capacity_envelope,
            throughput_target_percent=80,
        )
        return layer01, stack_result
    finally:
        if owns_session and session is not None and stack_result is not None:
            session.close(stack_result)


__all__ = [
    "LAYER_STACK_BUDGET_MS",
    "_Layer02To05Runner",
    "_LayerStackRunner",
    "run_full_from_cleanup_recon",
    "run_layers_02_to_05",
    "run_layers_02_to_06",
]
