"""Pure core orchestration for layers 2?? (Django-free).

The Django wrapper in ``django_apps.asteroid_lab.layers.stack_runner`` owns logs, settings, and
files; this core module is ignorant of them. It collects per-layer post-summary records into a
``CoreStackRunResult`` instead of writing them, so the caller decides whether/where to persist.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
        GeneticSampleSeedSnapshot,
    )

from shapez2_factory.application.asteroid_lab.layers.contracts.diagnostic import (
    DiagnosticLayerSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
    LayerPostSummaryRecord,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_result import StackRunResult
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from shapez2_factory.application.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    empty_layer04_rim_placement_result,
)
from shapez2_factory.application.asteroid_lab.layers.observability.post_summary_metrics import (
    build_layer02_post_summary_metrics,
    build_layer03_rim_greedy_post_summary_metrics,
    build_layer05_post_summary_metrics,
    build_layer06_post_summary_metrics,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

LAYER_STACK_BUDGET_MS = 60_000

_LAYER_INDEX: dict[str, int] = {
    LAYER_01_RECONSTRUCTION: 1,
    LAYER_02_EXTERIOR_TRANSPORT: 2,
    LAYER_03_RIM_GREEDY_PLACEMENT: 3,
    LAYER_03_RIM_MINING_BUNDLES: 3,  # deprecated alias; same index
    LAYER_04_RIM_BUNDLE_PLACEMENT: 4,  # inactive / reserved
    LAYER_05_INNER_PATTERN_FILL: 5,
    LAYER_06_COMMIT_VALIDATE: 6,
}


@dataclass(frozen=True, slots=True)
class _LayerStackRunner:
    slug: str
    run: Callable[..., Any]


# Backward-compatible alias (PR-3c).
_Layer02To05Runner = _LayerStackRunner


@dataclass(frozen=True, slots=True)
class CoreStackRunResult:
    """Pure stack outcome plus the ordered post-summary records the caller may persist."""

    stack_result: StackRunResult
    layer_summaries: tuple[LayerPostSummaryRecord, ...]


def _diagnostic_for_slug(slug: str) -> DiagnosticLayerSnapshot:
    return DiagnosticLayerSnapshot(
        layer_slug=slug,
        layer_index=_LAYER_INDEX.get(slug, 0),
        payload={"stub": True},
    )


def run_layers_02_to_06(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_LayerStackRunner, ...],
    genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
    capacity_envelope: dict[str, Any] | None = None,
    throughput_target_percent: int | None = None,
) -> CoreStackRunResult:
    completed: list[str] = []
    last_diagnostic: DiagnosticLayerSnapshot | None = None
    last_exterior_plan: ExteriorConnectionPlan | None = None
    last_rim_greedy: IntegratedRimGreedyResult | None = None
    summaries: list[LayerPostSummaryRecord] = []

    for entry in runners:
        if budget_ctx.remaining_budget_ms() <= 0:
            summaries.append(
                LayerPostSummaryRecord(
                    layer_slug=entry.slug,
                    layer_index=_LAYER_INDEX.get(entry.slug, 0),
                    outcome=LayerPostSummaryOutcome.SKIPPED_BUDGET,
                    elapsed_ms=0,
                    remaining_budget_ms=0,
                    metrics={"reason": "remaining_budget_ms_zero_before_start"},
                )
            )
            return CoreStackRunResult(
                stack_result=StackRunResult(
                    status=StackRunStatus.TIMEOUT_FAIL_CLOSED,
                    completed_layer_slugs=tuple(completed),
                    failed_layer_slug=entry.slug,
                    diagnostic_snapshot=last_diagnostic,
                ),
                layer_summaries=tuple(summaries),
            )
        started = budget_ctx.now_fn()
        post_metrics: dict[str, object] = {"stub": True}
        if entry.slug == LAYER_02_EXTERIOR_TRANSPORT:
            last_exterior_plan = entry.run(
                complete_map=complete_map,
                budget_ctx=budget_ctx,
                capacity_envelope=capacity_envelope,
                throughput_target_percent=throughput_target_percent,
            )
            if isinstance(last_exterior_plan, ExteriorConnectionPlan):
                post_metrics = build_layer02_post_summary_metrics(last_exterior_plan)
        elif entry.slug == LAYER_03_RIM_GREEDY_PLACEMENT:
            last_rim_greedy = entry.run(
                complete_map=complete_map,
                budget_ctx=budget_ctx,
                exterior_plan=last_exterior_plan,
                genetic_sample_seeds=genetic_sample_seeds,
            )
            if isinstance(last_rim_greedy, IntegratedRimGreedyResult):
                post_metrics = build_layer03_rim_greedy_post_summary_metrics(last_rim_greedy)
        elif entry.slug == LAYER_05_INNER_PATTERN_FILL:
            overlay = (
                last_rim_greedy.provisional_overlay
                if last_rim_greedy is not None
                else ProvisionalLayoutOverlay.empty()
            )
            placement_result = empty_layer04_rim_placement_result()
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
        summaries.append(
            LayerPostSummaryRecord(
                layer_slug=entry.slug,
                layer_index=_LAYER_INDEX.get(entry.slug, 0),
                outcome=LayerPostSummaryOutcome.COMPLETED,
                elapsed_ms=elapsed_ms,
                remaining_budget_ms=budget_ctx.remaining_budget_ms(),
                metrics=dict(post_metrics or {}),
            )
        )

    return CoreStackRunResult(
        stack_result=StackRunResult(
            status=StackRunStatus.SUCCESS,
            completed_layer_slugs=tuple(completed),
            failed_layer_slug=None,
            diagnostic_snapshot=None,
        ),
        layer_summaries=tuple(summaries),
    )


def run_layers_02_to_05(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_LayerStackRunner, ...],
    genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
    capacity_envelope: dict[str, Any] | None = None,
    throughput_target_percent: int | None = None,
) -> CoreStackRunResult:
    """Deprecated alias for ``run_layers_02_to_06`` (PR-3c layer renumber)."""
    return run_layers_02_to_06(
        complete_map=complete_map,
        budget_ctx=budget_ctx,
        runners=runners,
        genetic_sample_seeds=genetic_sample_seeds,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=throughput_target_percent,
    )


__all__ = [
    "LAYER_STACK_BUDGET_MS",
    "CoreStackRunResult",
    "_Layer02To05Runner",
    "_LayerStackRunner",
    "run_layers_02_to_05",
    "run_layers_02_to_06",
]
