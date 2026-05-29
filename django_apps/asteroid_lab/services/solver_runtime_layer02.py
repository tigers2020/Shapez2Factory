"""Solver runtime entry for Layer 02 only (L1 reconstruction + L2 exterior connectors)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    provenance_to_config_dict,
)
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
)
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from django_apps.asteroid_lab.layers.layer_01_reconstruction.run import run_layer_01
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.run import (
    execute_layer_02_exterior_transport_plan,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_timeline_frame_to_json_dict,
)
from django_apps.asteroid_lab.services import lab_replay_timeline_payload as lab_replay_payload
from django_apps.asteroid_lab.services.experiment_service import (
    create_or_replace_solver_run,
    create_solver_run,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_observability,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY,
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_types import (
    SolverRuntimeEntryErrorCode,
    SolverRuntimeEntryResult,
)


def parse_throughput_target_percent(
    config: dict[str, Any] | None,
) -> int | SolverRuntimeEntryErrorCode:
    """Return percent 1–100 or an error code."""

    if config is None:
        return 80
    raw = config.get(SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY)
    if raw is None:
        return 80
    try:
        pct = int(raw)
    except (TypeError, ValueError):
        return SolverRuntimeEntryErrorCode.INVALID_THROUGHPUT_TARGET_PERCENT
    if pct < 1 or pct > 100:
        return SolverRuntimeEntryErrorCode.INVALID_THROUGHPUT_TARGET_PERCENT
    return pct


def _default_run_key() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"lab-l2-{stamp}-{uuid.uuid4().hex[:8]}"


def _build_layer02_solver_summary(
    *,
    recon_observability: dict[str, Any],
    capacity_envelope: dict[str, Any],
    throughput_target_percent: int,
    plan_wire: dict[str, Any],
    planned_connector_count: int,
    unmet_reason: str | None,
    target_throughput_per_min: str,
) -> dict[str, Any]:
    required_connector_count = int(plan_wire.get("required_connector_count") or 0)
    required_planned = int(plan_wire.get("required_planned_count") or 0)
    run_success = unmet_reason is None and required_planned >= required_connector_count
    return {
        "validation_passed": False,
        "run_success": run_success,
        "capacity_satisfied": False,
        "placement_capacity_satisfied": False,
        "stack_run_status": StackRunStatus.SUCCESS.value,
        "completed_layer_slugs": [
            LAYER_01_RECONSTRUCTION,
            LAYER_02_EXTERIOR_TRANSPORT,
        ],
        "failed_layer_slug": None,
        "reconstruction_observability": recon_observability,
        "reconstruction_capacity": capacity_envelope,
        "throughput_target_percent": throughput_target_percent,
        "target_throughput_per_min": target_throughput_per_min,
        "exterior_connector_plan": plan_wire,
        "required_connector_count": plan_wire.get(
            "required_connector_count",
            planned_connector_count,
        ),
        "planned_connector_count": planned_connector_count,
        "layer_02_unmet_reason": unmet_reason,
        "algorithm_steps": ["layer_01_reconstruction", "layer_02_exterior_transport"],
    }


@transaction.atomic
def run_layer02_solver_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
    replace_existing_run: bool = False,
    config: dict[str, Any] | None = None,
    game_data_provenance: Any | None = None,
) -> SolverRuntimeEntryResult:
    """Run L1 facade + L2 exterior plan + L3 candidates + L4 provisional placement."""

    pid = int(project_id)
    pct = parse_throughput_target_percent(config)
    if isinstance(pct, SolverRuntimeEntryErrorCode):
        frames, metrics = build_lab_replay_frames_for_project(pid)
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            error_code=pct,
            message="throughput_target_percent must be an integer from 1 to 100",
        )

    inp = m.AsteroidMapInput.objects.filter(project_id=pid).order_by("-created_at", "-id").first()
    if inp is None:
        frames, metrics = build_lab_replay_frames_for_project(pid)
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
        )

    try:
        cleanup, recon = run_reconstruction_for_map_input(int(inp.pk))
    except Exception:  # noqa: BLE001
        frames, metrics = build_lab_replay_frames_for_project(pid)
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.DECODE_FAILED,
        )

    import time

    from django_apps.asteroid_lab.services.solver_layer_stack_log import (
        timed_ms,
        write_lab_solver_layer_stack_logs,
    )

    project = m.AsteroidProject.objects.filter(pk=pid).only("slug").first()
    project_slug = project.slug if project is not None else f"project-{pid}"

    t_l1 = time.monotonic()
    layer01 = run_layer_01(cleanup=cleanup, recon=recon)
    l1_elapsed_ms = timed_ms(t_l1)

    t_l2 = time.monotonic()
    plan = execute_layer_02_exterior_transport_plan(
        complete_map=layer01.complete_map,
        capacity_envelope=layer01.capacity_envelope,
        throughput_target_percent=pct,
    )
    l2_elapsed_ms = timed_ms(t_l2)
    plan_wire = exterior_connector_plan_to_metrics_dict(plan)["exterior_connector_plan"]
    unmet = plan.unmet_reason.value if plan.unmet_reason is not None else None
    planned_count = int(plan_wire.get("planned_connector_count") or len(plan.planned_connectors))

    obs = build_reconstruction_observability(
        recon=recon,
        complete_map=layer01.complete_map,
    )
    solver_summary = _build_layer02_solver_summary(
        recon_observability=obs,
        capacity_envelope=layer01.capacity_envelope,
        throughput_target_percent=pct,
        plan_wire=plan_wire,
        planned_connector_count=planned_count,
        unmet_reason=unmet,
        target_throughput_per_min=str(plan.planning_target_per_min),
    )

    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
        run_layer_03_rim_mining_bundles,
    )
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from django_apps.asteroid_lab.layers.stack_runner import LAYER_STACK_BUDGET_MS
    from django_apps.asteroid_lab.services.solver_runtime_rim_stack import (
        merge_rim_stack_into_solver_summary,
    )

    rim_budget = LayerBudgetContext.from_budget_ms(LAYER_STACK_BUDGET_MS)
    t_l3 = time.monotonic()
    layer03 = run_layer_03_rim_mining_bundles(
        complete_map=layer01.complete_map,
        exterior_plan=plan,
        budget_ctx=rim_budget,
    )
    l3_elapsed_ms = timed_ms(t_l3)
    t_l4 = time.monotonic()
    layer04 = run_layer_04_rim_bundle_placement(
        complete_map=layer01.complete_map,
        exterior_plan=plan,
        candidate_set=layer03,
        budget_ctx=rim_budget,
    )
    l4_elapsed_ms = timed_ms(t_l4)
    merge_rim_stack_into_solver_summary(
        solver_summary,
        layer03=layer03,
        layer04=layer04,
    )

    lab_serialized = [
        replay_timeline_frame_to_json_dict(fr)
        for fr in lab_replay_payload._lab_timeline_frames_for_project(pid)
    ]
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )

    runtime_replay_frames = build_solver_runtime_replay_frames(
        complete_map=layer01.complete_map,
        lab_frames_before_append=lab_serialized,
        exterior_plan_wire=plan_wire,
        layer03=layer03,
        layer04=layer04,
    )

    rk = (run_key or "").strip() or _default_run_key()

    completed_slugs = tuple(solver_summary.get("completed_layer_slugs") or ())
    log_dir = write_lab_solver_layer_stack_logs(
        project_slug=project_slug,
        run_key=rk,
        layer01=layer01,
        exterior_plan=plan,
        layer03=layer03,
        layer04=layer04,
        completed_layer_slugs=completed_slugs,
        layer01_elapsed_ms=l1_elapsed_ms,
        layer02_elapsed_ms=l2_elapsed_ms,
        layer03_elapsed_ms=l3_elapsed_ms,
        layer04_elapsed_ms=l4_elapsed_ms,
    )
    if log_dir is not None:
        solver_summary["layer_stack_log_dir"] = log_dir
    config_json: dict[str, Any] = {
        SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: solver_summary,
        SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY: pct,
        SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY: runtime_replay_frames,
        "exterior_connector_plan": plan_wire,
    }
    if isinstance(game_data_provenance, GameDataSnapshotProvenance):
        config_json[SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY] = (
            provenance_to_config_dict(game_data_provenance)
        )

    if replace_existing_run:
        dto = create_or_replace_solver_run(
            pid,
            run_key=rk,
            algorithm_label="layer_02_exterior_transport",
            config=config_json,
        )
        run_id = int(dto.id)
    else:
        dto = create_solver_run(
            pid,
            run_key=rk,
            algorithm_label="layer_02_exterior_transport",
            config=config_json,
        )
        run_id = int(dto.id)

    run = m.SolverRun.objects.filter(pk=run_id).first()
    if run is not None:
        run.status = (
            m.SolverRun.RunStatus.COMPLETED if unmet is None else m.SolverRun.RunStatus.PARTIAL
        )
        run.save(update_fields=["status"])

    frames, metrics = build_lab_replay_frames_for_project(pid, solver_run_id=run_id)
    return SolverRuntimeEntryResult(
        ok=True,
        solver_run_id=run_id,
        lab_replay_frames_json=frames,
        replay_track_metrics=metrics,
        solver_summary=solver_summary,
        validation_passed=False,
    )


__all__ = [
    "parse_throughput_target_percent",
    "run_layer02_solver_for_project",
]
