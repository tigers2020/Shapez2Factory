"""Orchestrates layer 1 facade and layers 2–5 with exclusive 60s budget."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.layers.contracts.diagnostic import DiagnosticLayerSnapshot
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_COMMIT_VALIDATE,
)
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
from django_apps.asteroid_lab.layers.layer_04_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)
from django_apps.asteroid_lab.layers.layer_05_commit_validate.run import (
    run_layer_05_commit_validate,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult

LAYER_STACK_BUDGET_MS = 60_000

_LAYER_INDEX: dict[str, int] = {
    LAYER_02_EXTERIOR_TRANSPORT: 2,
    LAYER_03_RIM_MINING_BUNDLES: 3,
    LAYER_04_INNER_PATTERN_FILL: 4,
    LAYER_05_COMMIT_VALIDATE: 5,
}


@dataclass(frozen=True, slots=True)
class _Layer02To05Runner:
    slug: str
    run: Callable[..., None]


_DEFAULT_RUNNERS: tuple[_Layer02To05Runner, ...] = (
    _Layer02To05Runner(LAYER_02_EXTERIOR_TRANSPORT, run_layer_02_exterior_transport),
    _Layer02To05Runner(LAYER_03_RIM_MINING_BUNDLES, run_layer_03_rim_mining_bundles),
    _Layer02To05Runner(LAYER_04_INNER_PATTERN_FILL, run_layer_04_inner_pattern_fill),
    _Layer02To05Runner(LAYER_05_COMMIT_VALIDATE, run_layer_05_commit_validate),
)


def _diagnostic_for_slug(slug: str) -> DiagnosticLayerSnapshot:
    return DiagnosticLayerSnapshot(
        layer_slug=slug,
        layer_index=_LAYER_INDEX[slug],
        payload={"stub": True},
    )


def run_layers_02_to_05(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    runners: tuple[_Layer02To05Runner, ...] = _DEFAULT_RUNNERS,
) -> StackRunResult:
    completed: list[str] = []
    last_diagnostic: DiagnosticLayerSnapshot | None = None

    for entry in runners:
        if budget_ctx.remaining_budget_ms() <= 0:
            return StackRunResult(
                status=StackRunStatus.TIMEOUT_FAIL_CLOSED,
                completed_layer_slugs=tuple(completed),
                failed_layer_slug=entry.slug,
                diagnostic_snapshot=last_diagnostic,
            )
        entry.run(complete_map=complete_map, budget_ctx=budget_ctx)
        completed.append(entry.slug)
        last_diagnostic = _diagnostic_for_slug(entry.slug)

    return StackRunResult(
        status=StackRunStatus.SUCCESS,
        completed_layer_slugs=tuple(completed),
        failed_layer_slug=None,
        diagnostic_snapshot=None,
    )


def run_full_from_cleanup_recon(
    *,
    cleanup: CleanupResult,
    recon: ReconstructionResult,
    budget_ctx: LayerBudgetContext | None = None,
    runners: tuple[_Layer02To05Runner, ...] = _DEFAULT_RUNNERS,
) -> tuple[Layer01ReconstructionOutput, StackRunResult]:
    layer01 = run_layer_01(cleanup=cleanup, recon=recon)
    ctx = budget_ctx or LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS)
    stack_result = run_layers_02_to_05(
        complete_map=layer01.complete_map,
        budget_ctx=ctx,
        runners=runners,
    )
    return layer01, stack_result


__all__ = [
    "LAYER_STACK_BUDGET_MS",
    "run_full_from_cleanup_recon",
    "run_layers_02_to_05",
]
