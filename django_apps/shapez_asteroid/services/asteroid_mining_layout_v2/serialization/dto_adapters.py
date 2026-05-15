"""Domain / runtime DTO → public JSON-safe dicts for behavior artifacts (output only)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.reconstruction import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    diagnostics as _recon_diag,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)
from django_apps.shapez_core.services.shapez_copy_decode import DecodeTraceResult

from .json_safe import to_jsonable
from .public_artifacts import (
    ARTIFACT_KIND_COPY_PREVIEW_BEHAVIOR,
    COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION,
    copy_preview_behavior_source_dict,
)


def decode_trace_to_public_dict(trace: DecodeTraceResult) -> dict[str, Any]:
    return {
        "steps": list(trace.steps),
        "success": trace.success,
        "error": trace.error,
    }


def preview_frames_thin_for_behavior_artifact(
    preview_frames: list[dict[str, Any]] | list[Any],
) -> list[dict[str, Any]]:
    """Behavior artifact stores only ``id`` + ``summary`` per preview frame (no ``mining_map``)."""

    return [
        {"id": fr.get("id"), "summary": fr.get("summary")}
        for fr in preview_frames
        if isinstance(fr, dict)
    ]


def pass1_replay_events_shallow_copy(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(e) for e in events]


def trace_event_to_public_dict(ev: TraceEvent) -> dict[str, Any]:
    """JSON-safe ``TraceEvent`` row for behavior artifacts (output-only)."""

    def _norm(val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, Enum):
            return val.value
        return val

    return {
        "run_id": ev.run_id,
        "phase": ev.phase,
        "step_index": ev.step_index,
        "event_type": ev.event_type,
        "committed": ev.committed,
        "commit_reason": _norm(ev.commit_reason),
        "rejected_reason": _norm(ev.rejected_reason),
        "rollback_reason": _norm(ev.rollback_reason),
        "recovery_trigger": _norm(ev.recovery_trigger),
        "computation_cycle": ev.computation_cycle,
        "route_level": ev.route_level,
        "transport_kind": _norm(ev.transport_kind),
    }


def runtime_trace_events_for_behavior_artifact(
    events: tuple[TraceEvent, ...] | list[TraceEvent],
) -> tuple[list[dict[str, Any]], bool]:
    """Return ``(public_rows, truncated)``; Slice 4 does not truncate (second value is false)."""

    rows = [trace_event_to_public_dict(e) for e in events]
    return rows, False


def try_step_1_diagnosis_for_empty_mineable(
    decoded_for_diagnosis: dict[str, Any],
    reconstruction_dto: ReconstructionDTO,
) -> tuple[Any, str | None]:
    """Run STEP 1 empty-mineable diagnostics for ``step_1_diagnosis`` (observability-only)."""

    try:
        dto = _recon_diag.diagnose_reconstruction_mineable_empty(
            decoded_for_diagnosis,
            reconstruction=reconstruction_dto,
        )
        return to_jsonable(dto), None
    except Exception as exc:  # noqa: BLE001 — diagnostics are observability-only
        return None, f"{type(exc).__name__}:{exc}"


def _generated_utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def assemble_copy_preview_behavior_document(
    *,
    input_digest_prefix: str,
    decode_trace: dict[str, Any],
    step_0_5: dict[str, Any] | None,
    step_1: Any,
    step_1_diagnosis: Any,
    step_1_diagnosis_error: str | None,
    preview_frames_thin: list[dict[str, Any]],
    pass1_replay_events: list[dict[str, Any]],
    runtime_trace_events: list[dict[str, Any]],
    runtime_trace_events_truncated: bool,
    partial_pipeline: dict[str, Any] | None,
    preview_schema_version: int | None,
    reconstruction_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    """Assemble the copy-preview behavior artifact root dict (stable key set)."""

    now = _generated_utc_now()
    events = list(pass1_replay_events)
    rt_events = list(runtime_trace_events)
    return {
        "schema_version": COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND_COPY_PREVIEW_BEHAVIOR,
        "generated_utc": now,
        "algorithm_input": False,
        "http_response_included": False,
        "includes_mining_map": False,
        "includes_full_pass1_events": True,
        "source": copy_preview_behavior_source_dict(),
        "input_digest_prefix": input_digest_prefix,
        "decode_trace": decode_trace,
        "step_0_5": step_0_5,
        "step_1": step_1,
        "step_1_diagnosis": step_1_diagnosis,
        "step_1_diagnosis_error": step_1_diagnosis_error,
        "preview_frames": preview_frames_thin,
        "pass1_replay_events": events,
        "pass1_replay_event_count": len(events),
        "pass1_replay_events_truncated": False,
        "runtime_trace_events": rt_events,
        "runtime_trace_event_count": len(rt_events),
        "runtime_trace_events_truncated": runtime_trace_events_truncated,
        "notes": {
            "partial_pipeline": partial_pipeline,
            "preview_schema_version": preview_schema_version,
            "reconstruction_summary": reconstruction_summary,
        },
    }


def build_decode_failure_behavior_document(
    *,
    trace: DecodeTraceResult,
    input_digest_prefix: str,
) -> dict[str, Any]:
    """Minimal artifact when decode fails (output-only; no blueprint JSON)."""

    now = _generated_utc_now()
    return {
        "schema_version": COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND_COPY_PREVIEW_BEHAVIOR,
        "generated_utc": now,
        "algorithm_input": False,
        "http_response_included": False,
        "includes_mining_map": False,
        "includes_full_pass1_events": True,
        "source": copy_preview_behavior_source_dict(),
        "input_digest_prefix": input_digest_prefix,
        "decode_trace": decode_trace_to_public_dict(trace),
        "step_0_5": None,
        "step_1": None,
        "step_1_diagnosis": None,
        "step_1_diagnosis_error": None,
        "preview_frames": [],
        "pass1_replay_events": [],
        "pass1_replay_event_count": 0,
        "pass1_replay_events_truncated": False,
        "runtime_trace_events": [],
        "runtime_trace_event_count": 0,
        "runtime_trace_events_truncated": False,
        "notes": {"decode_failed": True},
    }


__all__ = [
    "assemble_copy_preview_behavior_document",
    "build_decode_failure_behavior_document",
    "decode_trace_to_public_dict",
    "pass1_replay_events_shallow_copy",
    "preview_frames_thin_for_behavior_artifact",
    "runtime_trace_events_for_behavior_artifact",
    "trace_event_to_public_dict",
    "try_step_1_diagnosis_for_empty_mineable",
]
