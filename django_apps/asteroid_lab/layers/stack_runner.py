"""Orchestrates layer 1 facade and layers 2–6 with exclusive 60s budget."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    RimBundleCandidateSet,
    build_rim_bundle_candidate_set,
)
from django_apps.asteroid_lab.layers.contracts.diagnostic import DiagnosticLayerSnapshot
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_post_summary import LayerPostSummaryOutcome
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from django_apps.asteroid_lab.layers.layer_01_reconstruction.output import (
    Layer01ReconstructionOutput,
)
from django_apps.asteroid_lab.layers.layer_01_reconstruction.run import run_layer_01
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.run import (
    run_layer_02_exterior_transport,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
    run_layer_03_rim_mining_bundles,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    run_layer_04_rim_bundle_placement,
)
from django_apps.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_05_inner_pattern_fill,
)
from django_apps.asteroid_lab.layers.layer_06_commit_validate.run import (
    run_layer_06_commit_validate,
)
from django_apps.asteroid_lab.layers.observability.layer_post_summary_log import (
    LayerPostSummaryLogSession,
    build_layer01_post_summary_metrics,
    build_layer02_post_summary_metrics,
    build_layer03_post_summary_metrics,
    build_layer04_post_summary_metrics,
    build_layer05_post_summary_metrics,
    build_layer06_post_summary_metrics,
    create_layer_post_summary_log_session,
    emit_layer_post_summary,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult

LAYER_STACK_BUDGET_MS = 60_000

_LAYER_INDEX: dict[str, int] = {
    LAYER_01_RECONSTRUCTION: 1,
    LAYER_02_EXTERIOR_TRANSPORT: 2,
    LAYER_03_RIM_MINING_BUNDLES: 3,
    LAYER_04_RIM_BUNDLE_PLACEMENT: 4,
    LAYER_05_INNER_PATTERN_FILL: 5,
    LAYER_06_COMMIT_VALIDATE: 6,
}


def _empty_candidate_set() -> RimBundleCandidateSet:
    from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
        build_layer03_observability,
    )

    metrics = Layer03ExpansionMetrics.empty()
    return build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=metrics,
        observability=build_layer03_observability(metrics=metrics, normal_candidates=()),
    )


@dataclass(frozen=True, slots=True)
class _LayerStackRunner:
    slug: str
    run: Callable[..., Any]


# Backward-compatible alias (PR-3c).
_Layer02To05Runner = _LayerStackRunner


_DEFAULT_RUNNERS: tuple[_LayerStackRunner, ...] = (
    _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, run_layer_02_exterior_transport),
    _LayerStackRunner(LAYER_03_RIM_MINING_BUNDLES, run_layer_03_rim_mining_bundles),
    _LayerStackRunner(LAYER_04_RIM_BUNDLE_PLACEMENT, run_layer_04_rim_bundle_placement),
    _LayerStackRunner(LAYER_05_INNER_PATTERN_FILL, run_layer_05_inner_pattern_fill),
    _LayerStackRunner(LAYER_06_COMMIT_VALIDATE, run_layer_06_commit_validate),
)


def _diagnostic_for_slug(slug: str) -> DiagnosticLayerSnapshot:
    return DiagnosticLayerSnapshot(
        layer_slug=slug,
        layer_index=_LAYER_INDEX[slug],
        payload={"stub": True},
    )


def run_layers_02_to_06(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_LayerStackRunner, ...] = _DEFAULT_RUNNERS,
    post_summary_session: LayerPostSummaryLogSession | None = None,
) -> StackRunResult:
    completed: list[str] = []
    last_diagnostic: DiagnosticLayerSnapshot | None = None
    last_exterior_plan: ExteriorConnectionPlan | None = None
    last_candidate_set: RimBundleCandidateSet = _empty_candidate_set()
    last_placement_result: Layer04RimPlacementResult | None = None

    for entry in runners:
        if budget_ctx.remaining_budget_ms() <= 0:
            emit_layer_post_summary(
                post_summary_session,
                layer_slug=entry.slug,
                layer_index=_LAYER_INDEX.get(entry.slug, 0),
                outcome=LayerPostSummaryOutcome.SKIPPED_BUDGET,
                elapsed_ms=0,
                remaining_budget_ms=0,
                metrics={"reason": "remaining_budget_ms_zero_before_start"},
            )
            return StackRunResult(
                status=StackRunStatus.TIMEOUT_FAIL_CLOSED,
                completed_layer_slugs=tuple(completed),
                failed_layer_slug=entry.slug,
                diagnostic_snapshot=last_diagnostic,
            )
        started = budget_ctx.now_fn()
        post_metrics: dict[str, object] = {"stub": True}
        if entry.slug == LAYER_02_EXTERIOR_TRANSPORT:
            last_exterior_plan = entry.run(complete_map=complete_map, budget_ctx=budget_ctx)
            if isinstance(last_exterior_plan, ExteriorConnectionPlan):
                post_metrics = build_layer02_post_summary_metrics(last_exterior_plan)
        elif entry.slug == LAYER_03_RIM_MINING_BUNDLES:
            layer03_result = entry.run(
                complete_map=complete_map,
                budget_ctx=budget_ctx,
                exterior_plan=last_exterior_plan,
            )
            if isinstance(layer03_result, RimBundleCandidateSet):
                last_candidate_set = layer03_result
                post_metrics = build_layer03_post_summary_metrics(layer03_result)
        elif entry.slug == LAYER_04_RIM_BUNDLE_PLACEMENT:
            last_placement_result = entry.run(
                complete_map=complete_map,
                exterior_plan=last_exterior_plan,
                candidate_set=last_candidate_set,
                budget_ctx=budget_ctx,
            )
            if isinstance(last_placement_result, Layer04RimPlacementResult):
                post_metrics = build_layer04_post_summary_metrics(last_placement_result)
        elif entry.slug == LAYER_05_INNER_PATTERN_FILL:
            overlay = (
                last_placement_result.provisional_overlay
                if last_placement_result is not None
                else ProvisionalLayoutOverlay.empty()
            )
            from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
                empty_layer04_rim_placement_result,
            )

            placement_result = (
                last_placement_result
                if last_placement_result is not None
                else empty_layer04_rim_placement_result()
            )
            entry.run(
                complete_map=complete_map,
                exterior_plan=last_exterior_plan,
                rim_placement_result=placement_result,
                provisional_overlay=overlay,
                budget_ctx=budget_ctx,
            )
            post_metrics = build_layer05_post_summary_metrics()
        elif entry.slug == LAYER_06_COMMIT_VALIDATE:
            entry.run(complete_map=complete_map, budget_ctx=budget_ctx)
            post_metrics = build_layer06_post_summary_metrics()
        else:
            entry.run(complete_map=complete_map, budget_ctx=budget_ctx)
        elapsed_ms = max(0, int((budget_ctx.now_fn() - started) * 1000))
        completed.append(entry.slug)
        last_diagnostic = _diagnostic_for_slug(entry.slug)
        emit_layer_post_summary(
            post_summary_session,
            layer_slug=entry.slug,
            layer_index=_LAYER_INDEX.get(entry.slug, 0),
            outcome=LayerPostSummaryOutcome.COMPLETED,
            elapsed_ms=elapsed_ms,
            remaining_budget_ms=budget_ctx.remaining_budget_ms(),
            metrics=post_metrics,
        )

    return StackRunResult(
        status=StackRunStatus.SUCCESS,
        completed_layer_slugs=tuple(completed),
        failed_layer_slug=None,
        diagnostic_snapshot=None,
    )


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
