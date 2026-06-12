"""Pure core orchestration for layers 2–6 (Django-free).

The Django wrapper in ``django_apps.asteroid_lab.layers.stack_runner`` owns logs, settings, and
files; this core module is ignorant of them. It collects per-layer post-summary records into a
``CoreStackRunResult`` instead of writing them, so the caller decides whether/where to persist.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
        GeneticSampleSeedSnapshot,
    )
    from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
        SpaceTransportTileCatalog,
    )

from shapez2_factory.application.asteroid_lab.layers.contracts.diagnostic import (
    DiagnosticLayerSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04InnerFillResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05RoutePlan,
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
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_04_TRANSPORT_ROUTING,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYER_06_COMMIT_VALIDATE,
    resolve_canonical_layer_slug,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_result import StackRunResult
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from shapez2_factory.application.asteroid_lab.layers.observability.layer05_post_summary_metrics import (  # noqa: E501
    build_layer05_transport_post_summary_metrics,
)
from shapez2_factory.application.asteroid_lab.layers.observability.post_summary_metrics import (
    build_layer02_post_summary_metrics,
    build_layer03_rim_greedy_post_summary_metrics,
    build_layer04_inner_fill_post_summary_metrics,
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
    LAYER_03_RIM_MINING_BUNDLES: 3,
    LAYER_04_RIM_BUNDLE_PLACEMENT: 4,
    LAYER_04_INNER_PATTERN_FILL: 4,
    LAYER_04_TRANSPORT_ROUTING: 4,  # deprecated slug literal
    LAYER_05_INNER_PATTERN_FILL: 5,  # deprecated slug literal
    LAYER_05_TRANSPORT_ROUTING: 5,
    LAYER_06_COMMIT_VALIDATE: 6,
}


@dataclass(frozen=True, slots=True)
class _LayerStackRunner:
    slug: str
    run: Callable[..., object]


# Backward-compatible alias (PR-3c).
_Layer02To05Runner = _LayerStackRunner


@dataclass(frozen=True, slots=True)
class CoreStackRunResult:
    """Pure stack outcome plus the ordered post-summary records the caller may persist."""

    stack_result: StackRunResult
    layer_summaries: tuple[LayerPostSummaryRecord, ...]
    exterior_plan: ExteriorConnectionPlan | None = None
    rim_greedy: IntegratedRimGreedyResult | None = None
    inner_fill: Layer04InnerFillResult | None = None
    route_plan: Layer05RoutePlan | None = None


def _diagnostic_for_slug(slug: str) -> DiagnosticLayerSnapshot:
    canonical = resolve_canonical_layer_slug(slug)
    return DiagnosticLayerSnapshot(
        layer_slug=slug,
        layer_index=_LAYER_INDEX.get(canonical, _LAYER_INDEX.get(slug, 0)),
        payload={"stub": True},
    )


def _layer_index_for_slug(slug: str) -> int:
    canonical = resolve_canonical_layer_slug(slug)
    return _LAYER_INDEX.get(canonical, _LAYER_INDEX.get(slug, 0))


def run_layers_02_to_06(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_LayerStackRunner, ...],
    genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
    capacity_envelope: dict[str, object] | None = None,
    throughput_target_percent: int | None = None,
    transport_catalog: SpaceTransportTileCatalog | None = None,
) -> CoreStackRunResult:
    completed: list[str] = []
    last_diagnostic: DiagnosticLayerSnapshot | None = None
    last_exterior_plan: ExteriorConnectionPlan | None = None
    last_rim_greedy: IntegratedRimGreedyResult | None = None
    last_inner_fill: Layer04InnerFillResult | None = None
    last_layer05_plan: Layer05RoutePlan | None = None
    summaries: list[LayerPostSummaryRecord] = []

    for entry in runners:
        canonical_slug = resolve_canonical_layer_slug(entry.slug)
        if budget_ctx.remaining_budget_ms() <= 0:
            summaries.append(
                LayerPostSummaryRecord(
                    layer_slug=entry.slug,
                    layer_index=_layer_index_for_slug(entry.slug),
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
                exterior_plan=last_exterior_plan,
                rim_greedy=last_rim_greedy,
                inner_fill=last_inner_fill,
                route_plan=last_layer05_plan,
            )
        started = budget_ctx.now_fn()
        post_metrics: dict[str, object] = {"stub": True}
        if canonical_slug == LAYER_02_EXTERIOR_TRANSPORT:
            layer02_result = entry.run(
                complete_map=complete_map,
                budget_ctx=budget_ctx,
                capacity_envelope=capacity_envelope,
                throughput_target_percent=throughput_target_percent,
            )
            if isinstance(layer02_result, ExteriorConnectionPlan):
                last_exterior_plan = layer02_result
                post_metrics = build_layer02_post_summary_metrics(layer02_result)
        elif canonical_slug == LAYER_03_RIM_GREEDY_PLACEMENT:
            layer03_result = entry.run(
                complete_map=complete_map,
                budget_ctx=budget_ctx,
                exterior_plan=last_exterior_plan,
                genetic_sample_seeds=genetic_sample_seeds,
            )
            if isinstance(layer03_result, IntegratedRimGreedyResult):
                last_rim_greedy = layer03_result
                post_metrics = build_layer03_rim_greedy_post_summary_metrics(layer03_result)
        elif canonical_slug == LAYER_04_INNER_PATTERN_FILL:
            overlay = (
                last_rim_greedy.provisional_overlay
                if last_rim_greedy is not None
                else ProvisionalLayoutOverlay.empty()
            )
            layer04_result = entry.run(
                complete_map=complete_map,
                exterior_plan=last_exterior_plan,
                provisional_overlay=overlay,
                budget_ctx=budget_ctx,
            )
            if isinstance(layer04_result, Layer04InnerFillResult):
                last_inner_fill = layer04_result
                post_metrics = build_layer04_inner_fill_post_summary_metrics(layer04_result)
        elif canonical_slug == LAYER_05_TRANSPORT_ROUTING:
            resource_kind = (
                last_exterior_plan.transport_kind if last_exterior_plan is not None else "shape"
            )
            interior = (
                last_inner_fill.interior_occupied_cells
                if last_inner_fill is not None
                else frozenset()
            )
            layer05_result = entry.run(
                complete_map=complete_map,
                exterior_plan=last_exterior_plan,
                rim_result=last_rim_greedy,
                resource_kind=resource_kind,
                budget_ctx=budget_ctx,
                transport_catalog=transport_catalog,
                interior_occupied_cells=interior,
                inner_fill=last_inner_fill,
            )
            if isinstance(layer05_result, Layer05RoutePlan):
                last_layer05_plan = layer05_result
                post_metrics = build_layer05_transport_post_summary_metrics(layer05_result)
        elif canonical_slug == LAYER_06_COMMIT_VALIDATE:
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
                layer_index=_layer_index_for_slug(entry.slug),
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
        exterior_plan=last_exterior_plan,
        rim_greedy=last_rim_greedy,
        inner_fill=last_inner_fill,
        route_plan=last_layer05_plan,
    )


def run_layers_02_to_05(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_LayerStackRunner, ...],
    genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
    capacity_envelope: dict[str, object] | None = None,
    throughput_target_percent: int | None = None,
    transport_catalog: SpaceTransportTileCatalog | None = None,
) -> CoreStackRunResult:
    """Deprecated alias for ``run_layers_02_to_06`` (PR-3c layer renumber)."""
    return run_layers_02_to_06(
        complete_map=complete_map,
        budget_ctx=budget_ctx,
        runners=runners,
        genetic_sample_seeds=genetic_sample_seeds,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=throughput_target_percent,
        transport_catalog=transport_catalog,
    )


__all__ = [
    "LAYER_STACK_BUDGET_MS",
    "CoreStackRunResult",
    "_Layer02To05Runner",
    "_LayerStackRunner",
    "run_layers_02_to_05",
    "run_layers_02_to_06",
]
