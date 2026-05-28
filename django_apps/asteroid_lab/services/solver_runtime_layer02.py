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
from django_apps.asteroid_lab.services.lab_layer02_timeline import (
    build_layer02_runtime_replay_frames,
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
    run_success = unmet_reason is None and planned_connector_count > 0
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
    """Run L1 facade + L2 exterior connector plan; L3–L5 remain unrun (holding)."""

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

    layer01 = run_layer_01(cleanup=cleanup, recon=recon)
    plan = execute_layer_02_exterior_transport_plan(
        complete_map=layer01.complete_map,
        capacity_envelope=layer01.capacity_envelope,
        throughput_target_percent=pct,
    )
    plan_wire = exterior_connector_plan_to_metrics_dict(plan)["exterior_connector_plan"]
    unmet = plan.unmet_reason.value if plan.unmet_reason is not None else None
    planned_count = len(plan.planned_connectors)

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

    lab_serialized = [
        replay_timeline_frame_to_json_dict(fr)
        for fr in lab_replay_payload._lab_timeline_frames_for_project(pid)
    ]
    runtime_replay_frames = build_layer02_runtime_replay_frames(
        plan_wire=plan_wire,
        lab_frames_before_append=lab_serialized,
        complete_map=layer01.complete_map,
    )

    rk = (run_key or "").strip() or _default_run_key()
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
