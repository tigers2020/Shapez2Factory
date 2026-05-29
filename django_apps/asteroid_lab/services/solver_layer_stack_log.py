"""Write per-layer JSONL logs for Lab solver runtime (observability only)."""

from __future__ import annotations

import time

from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_post_summary import LayerPostSummaryOutcome
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
)
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from django_apps.asteroid_lab.layers.layer_01_reconstruction.output import (
    Layer01ReconstructionOutput,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.forensic_log import (
    write_layer04_selected_placements_log,
)
from django_apps.asteroid_lab.layers.observability.layer_post_summary_log import (
    build_layer01_post_summary_metrics,
    build_layer02_post_summary_metrics,
    build_layer03_post_summary_metrics,
    build_layer04_post_summary_metrics,
    create_layer_post_summary_log_session,
    emit_layer_post_summary,
)

_LAYER_INDEX = {
    LAYER_01_RECONSTRUCTION: 1,
    LAYER_02_EXTERIOR_TRANSPORT: 2,
    LAYER_03_RIM_MINING_BUNDLES: 3,
    LAYER_04_RIM_BUNDLE_PLACEMENT: 4,
}


def write_lab_solver_layer_stack_logs(
    *,
    project_slug: str,
    run_key: str,
    layer01: Layer01ReconstructionOutput,
    exterior_plan: ExteriorConnectionPlan,
    layer03: RimBundleCandidateSet,
    layer04: Layer04RimPlacementResult,
    completed_layer_slugs: tuple[str, ...],
    failed_layer_slug: str | None = None,
    stack_run_status: StackRunStatus = StackRunStatus.SUCCESS,
    solver_run_id: int | None = None,
    layer01_elapsed_ms: int | None = None,
    layer02_elapsed_ms: int | None = None,
    layer03_elapsed_ms: int | None = None,
    layer04_elapsed_ms: int | None = None,
) -> str | None:
    """Persist L1–L4 behavior + summary JSONL under var/; return run log dir or None."""

    session = create_layer_post_summary_log_session(
        project_slug=project_slug,
        run_id=run_key,
        solver_run_id=solver_run_id,
    )
    if session is None:
        return None

    emit_layer_post_summary(
        session,
        layer_slug=LAYER_01_RECONSTRUCTION,
        layer_index=_LAYER_INDEX[LAYER_01_RECONSTRUCTION],
        outcome=LayerPostSummaryOutcome.COMPLETED,
        elapsed_ms=layer01_elapsed_ms or 0,
        remaining_budget_ms=None,
        metrics=build_layer01_post_summary_metrics(layer01),
    )
    emit_layer_post_summary(
        session,
        layer_slug=LAYER_02_EXTERIOR_TRANSPORT,
        layer_index=_LAYER_INDEX[LAYER_02_EXTERIOR_TRANSPORT],
        outcome=LayerPostSummaryOutcome.COMPLETED,
        elapsed_ms=layer02_elapsed_ms or 0,
        remaining_budget_ms=None,
        metrics=build_layer02_post_summary_metrics(exterior_plan),
    )
    emit_layer_post_summary(
        session,
        layer_slug=LAYER_03_RIM_MINING_BUNDLES,
        layer_index=_LAYER_INDEX[LAYER_03_RIM_MINING_BUNDLES],
        outcome=LayerPostSummaryOutcome.COMPLETED,
        elapsed_ms=layer03_elapsed_ms or 0,
        remaining_budget_ms=None,
        metrics=build_layer03_post_summary_metrics(layer03),
    )
    emit_layer_post_summary(
        session,
        layer_slug=LAYER_04_RIM_BUNDLE_PLACEMENT,
        layer_index=_LAYER_INDEX[LAYER_04_RIM_BUNDLE_PLACEMENT],
        outcome=LayerPostSummaryOutcome.COMPLETED,
        elapsed_ms=layer04_elapsed_ms or 0,
        remaining_budget_ms=None,
        metrics=build_layer04_post_summary_metrics(layer04),
    )
    if layer04.selected_placements:
        write_layer04_selected_placements_log(
            run_dir=session.run_dir,
            selected_placements=layer04.selected_placements,
        )
    stack_result = StackRunResult(
        status=stack_run_status,
        completed_layer_slugs=completed_layer_slugs,
        failed_layer_slug=failed_layer_slug,
        diagnostic_snapshot=None,
    )
    session.close(stack_result)
    return str(session.run_dir)


def timed_ms(start: float) -> int:
    return max(0, int((time.monotonic() - start) * 1000))


__all__ = ["timed_ms", "write_lab_solver_layer_stack_logs"]
