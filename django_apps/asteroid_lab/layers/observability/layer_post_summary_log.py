"""JSONL post-summary writer per layer slug (flag-gated)."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

from django_apps.asteroid_lab.layers.contracts.layer_post_summary import LayerPostSummaryRecord
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.layer_01_reconstruction.output import (
    Layer01ReconstructionOutput,
)

_SCHEMA_VERSION = 1


def _settings_bool(name: str, default: bool = False) -> bool:
    raw = getattr(settings, name, default)
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


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


@dataclass
class LayerPostSummaryLogSession:
    """One stack run directory; one JSONL line per layer post summary."""

    run_id: str
    run_dir: Path
    project_slug: str | None = None
    solver_run_id: int | None = None

    def write_layer_post_summary(self, record: LayerPostSummaryRecord) -> None:
        row = {
            "schema_version": _SCHEMA_VERSION,
            "record_type": "layer_post_summary",
            "run_id": self.run_id,
            "project_slug": self.project_slug,
            "solver_run_id": self.solver_run_id,
            "layer_slug": record.layer_slug,
            "layer_index": record.layer_index,
            "outcome": record.outcome.value,
            "elapsed_ms": record.elapsed_ms,
            "remaining_budget_ms": record.remaining_budget_ms,
            "timestamp": timezone.localtime().isoformat(),
            "metrics": _json_safe(record.metrics),
        }
        path = self.run_dir / f"{_safe_slug(record.layer_slug)}.post_summary.jsonl"
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
            "timestamp": timezone.localtime().isoformat(),
        }
        path = self.run_dir / "stack_run.post_summary.jsonl"
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
        }
        path = self.run_dir / "manifest.json"
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )


def create_layer_post_summary_log_session(
    *,
    project_slug: str | None = None,
    solver_run_id: int | None = None,
    run_id: str | None = None,
) -> LayerPostSummaryLogSession | None:
    if not _settings_bool("ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED", False):
        return None
    root = Path(settings.ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_DIR)
    rid = run_id or _new_run_id()
    run_dir = root / "runs" / _safe_slug(rid)
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
    "create_layer_post_summary_log_session",
]
