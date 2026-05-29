"""JSONL layer behavior + post-summary logs under var/ (flag-gated, max N runs retained)."""

from __future__ import annotations

import json
import secrets
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
    LayerPostSummaryRecord,
)
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.layer_01_reconstruction.output import (
    Layer01ReconstructionOutput,
)
from django_apps.asteroid_lab.layers.observability.layer_behavior_catalog import (
    format_layer_summary_line,
    layer_behavior_for_slug,
)

_SCHEMA_VERSION = 2
_DEFAULT_MAX_RUNS = 5


def _settings_bool(name: str, default: bool = False) -> bool:
    raw = getattr(settings, name, default)
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _settings_int(name: str, default: int) -> int:
    raw = getattr(settings, name, default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


def _safe_slug(value: str) -> str:
    text = "".join(c if c.isalnum() or c in "._-" else "-" for c in value.strip())
    return text.strip("-") or "run"


def _new_run_id() -> str:
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    return f"layer-stack-{stamp}-{secrets.token_hex(3)}"


def _log_root() -> Path:
    return Path(settings.ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_DIR)


def _runs_parent(*, project_slug: str | None) -> Path:
    root = _log_root()
    if project_slug:
        return root / "projects" / _safe_slug(project_slug) / "runs"
    return root / "runs"


def _prune_old_runs(runs_parent: Path, *, max_runs: int) -> None:
    if max_runs < 1:
        return
    if not runs_parent.is_dir():
        return
    run_dirs = [p for p in runs_parent.iterdir() if p.is_dir()]
    if len(run_dirs) < max_runs:
        return
    run_dirs.sort(key=lambda p: p.stat().st_mtime)
    for stale in run_dirs[: len(run_dirs) - max_runs + 1]:
        shutil.rmtree(stale, ignore_errors=True)


def build_layer01_post_summary_metrics(
    layer01: Layer01ReconstructionOutput,
) -> dict[str, object]:
    complete = layer01.complete_map
    return {
        "complete_map_cell_count": len(complete.cells),
        "shape_field_cell_count": int(complete.shape_field_cell_count),
        "fluid_field_cell_count": int(complete.fluid_field_cell_count),
        "external_void_cell_count": len(complete.external_void_cells),
        "coord_frame": str(complete.coord_frame.value),
    }


def build_layer02_post_summary_metrics(plan: ExteriorConnectionPlan) -> dict[str, object]:
    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    spare_planned = len(plan.planned_connectors) - required_planned
    return {
        "transport_kind": plan.transport_kind,
        "terrain_upper_bound_per_min": str(plan.terrain_upper_bound_per_min),
        "planning_target_per_min": str(plan.planning_target_per_min),
        "required_connector_count": plan.required_connector_count,
        "reference_connector_count": plan.reference_connector_count,
        "spare_connector_count": plan.spare_connector_count,
        "planned_connector_count": len(plan.planned_connectors),
        "required_planned_count": required_planned,
        "spare_planned_count": spare_planned,
        "unmet_reason": plan.unmet_reason.value if plan.unmet_reason is not None else None,
    }


def build_layer03_post_summary_metrics(result: RimBundleCandidateSet) -> dict[str, object]:
    metrics = result.metrics
    return {
        "rim_anchor_count": metrics.rim_anchor_count,
        "seed_projection_attempt_count": metrics.seed_projection_attempt_count,
        "exterior_direction_candidate_count": metrics.exterior_direction_candidate_count,
        "direction_seed_attempt_count": metrics.direction_seed_attempt_count,
        "mining_footprint_prefilter_rejected_count": (
            metrics.mining_footprint_prefilter_rejected_count
        ),
        "local_geometry_rejected_count": metrics.local_geometry_rejected_count,
        "route_probe_attempt_count": metrics.route_probe_attempt_count,
        "route_probe_succeeded_count": metrics.route_probe_succeeded_count,
        "route_probe_failed_count": metrics.route_probe_failed_count,
        "dedupe_duplicate_count": metrics.dedupe_duplicate_count,
        "normal_candidate_count": metrics.normal_candidate_count,
        "diagnostic_rejected_count": metrics.diagnostic_rejected_count,
        "budget_skipped_count": metrics.budget_skipped_count,
        "layer_skip_reason": metrics.layer_skip_reason.value,
        "reject_reason_counts": list(metrics.reject_reason_counts),
        "field_route_cell_count_total": metrics.field_route_cell_count_total,
        "weighted_route_cost_total": metrics.weighted_route_cost_total,
        "transport_blocked_by_mining_count": metrics.transport_blocked_by_mining_count,
    }


def build_layer04_post_summary_metrics(result: Layer04RimPlacementResult) -> dict[str, object]:
    return {
        "selected_count": result.selected_count,
        "rejected_overlap_count": result.rejected_overlap_count,
        "rejected_budget_count": result.rejected_budget_count,
        "overlay_occupied_cell_count": len(result.provisional_overlay.occupied_cells),
    }


def build_layer05_post_summary_metrics() -> dict[str, object]:
    return {"stub": True}


def build_layer06_post_summary_metrics() -> dict[str, object]:
    return {"stub": True}


@dataclass
class LayerPostSummaryLogSession:
    """One stack run directory; one JSONL file per layer slug."""

    run_id: str
    run_dir: Path
    project_slug: str | None = None
    solver_run_id: int | None = None

    def write_layer_post_summary(self, record: LayerPostSummaryRecord) -> None:
        behavior = layer_behavior_for_slug(record.layer_slug)
        summary = format_layer_summary_line(
            record.layer_slug,
            outcome=record.outcome,
            metrics=record.metrics,
        )
        row = {
            "schema_version": _SCHEMA_VERSION,
            "record_type": "layer_post_summary",
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "layer_slug": record.layer_slug,
            "layer_index": record.layer_index,
            "behavior": behavior,
            "summary": summary,
            "outcome": record.outcome.value,
            "elapsed_ms": record.elapsed_ms,
            "remaining_budget_ms": record.remaining_budget_ms,
            "timestamp": timezone.localtime().isoformat(),
            "metrics": _json_safe(record.metrics),
        }
        path = self.run_dir / f"{_safe_slug(record.layer_slug)}.jsonl"
        data = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(data)

    def write_stack_run_post_summary(self, stack_result: StackRunResult) -> None:
        row = {
            "schema_version": _SCHEMA_VERSION,
            "record_type": "stack_run_post_summary",
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "stack_run_status": stack_result.status.value,
            "completed_layer_slugs": list(stack_result.completed_layer_slugs),
            "failed_layer_slug": stack_result.failed_layer_slug,
            "summary": (
                f"status={stack_result.status.value} "
                f"completed={len(stack_result.completed_layer_slugs)} "
                f"failed={stack_result.failed_layer_slug or 'none'}"
            ),
            "timestamp": timezone.localtime().isoformat(),
        }
        path = self.run_dir / "stack_run.jsonl"
        data = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(data)

    def close(self, stack_result: StackRunResult) -> None:
        self.write_stack_run_post_summary(stack_result)
        manifest = {
            "schema_version": _SCHEMA_VERSION,
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "stack_run_status": stack_result.status.value,
            "completed_layer_slugs": list(stack_result.completed_layer_slugs),
            "failed_layer_slug": stack_result.failed_layer_slug,
            "log_dir": str(self.run_dir),
        }
        path = self.run_dir / "manifest.json"
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )


def emit_layer_post_summary(
    session: LayerPostSummaryLogSession | None,
    *,
    layer_slug: str,
    layer_index: int,
    outcome: LayerPostSummaryOutcome,
    elapsed_ms: int,
    remaining_budget_ms: int | None,
    metrics: dict[str, object] | None = None,
) -> None:
    if session is None:
        return
    session.write_layer_post_summary(
        LayerPostSummaryRecord(
            layer_slug=layer_slug,
            layer_index=layer_index,
            outcome=outcome,
            elapsed_ms=elapsed_ms,
            remaining_budget_ms=remaining_budget_ms,
            metrics=dict(metrics or {}),
        )
    )


def create_layer_post_summary_log_session(
    *,
    project_slug: str | None = None,
    solver_run_id: int | None = None,
    run_id: str | None = None,
) -> LayerPostSummaryLogSession | None:
    if not _settings_bool("ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED", False):
        return None
    max_runs = _settings_int("ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_MAX_RUNS", _DEFAULT_MAX_RUNS)
    parent = _runs_parent(project_slug=project_slug)
    _prune_old_runs(parent, max_runs=max_runs)
    rid = run_id or _new_run_id()
    run_dir = parent / _safe_slug(rid)
    run_dir.mkdir(parents=True, exist_ok=True)
    return LayerPostSummaryLogSession(
        run_id=rid,
        run_dir=run_dir,
        project_slug=project_slug,
        solver_run_id=solver_run_id,
    )


__all__ = [
    "LayerPostSummaryLogSession",
    "build_layer01_post_summary_metrics",
    "build_layer02_post_summary_metrics",
    "build_layer03_post_summary_metrics",
    "build_layer04_post_summary_metrics",
    "build_layer05_post_summary_metrics",
    "build_layer06_post_summary_metrics",
    "create_layer_post_summary_log_session",
    "emit_layer_post_summary",
]
