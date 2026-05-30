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

from django_apps.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
    LayerPostSummaryRecord,
)
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.observability.layer_behavior_catalog import (
    format_layer_summary_line,
    layer_behavior_for_slug,
)
from shapez2_factory.application.asteroid_lab.layers.observability.post_summary_metrics import (
    build_layer01_post_summary_metrics,
    build_layer02_post_summary_metrics,
    build_layer03_post_summary_metrics,
    build_layer03_rim_greedy_post_summary_metrics,  # noqa: F401  (re-export; not in __all__)
    build_layer05_post_summary_metrics,
    build_layer06_post_summary_metrics,
)

_SCHEMA_VERSION = 2
_DEFAULT_MAX_RUNS = 5
_LAYER04_SELECTED_PLACEMENTS_FILENAME = "layer_04_selected_placements.jsonl"


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


def build_layer04_post_summary_metrics(result: Layer04RimPlacementResult) -> dict[str, object]:
    return {
        "selected_count": result.selected_count,
        "rejected_overlap_count": result.rejected_overlap_count,
        "rejected_budget_count": result.rejected_budget_count,
        "overlay_occupied_cell_count": len(result.provisional_overlay.occupied_cells),
    }


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
        artifacts: dict[str, str] = {}
        forensic_path = self.run_dir / _LAYER04_SELECTED_PLACEMENTS_FILENAME
        if forensic_path.is_file():
            artifacts["layer04_selected_placements"] = _LAYER04_SELECTED_PLACEMENTS_FILENAME
        manifest: dict[str, object] = {
            "schema_version": _SCHEMA_VERSION,
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "stack_run_status": stack_result.status.value,
            "completed_layer_slugs": list(stack_result.completed_layer_slugs),
            "failed_layer_slug": stack_result.failed_layer_slug,
            "log_dir": str(self.run_dir),
        }
        if artifacts:
            manifest["artifacts"] = artifacts
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
