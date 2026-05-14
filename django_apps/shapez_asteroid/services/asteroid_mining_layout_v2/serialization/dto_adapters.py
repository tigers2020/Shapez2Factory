"""Domain / runtime DTO → public JSON-safe dicts for behavior artifacts (output only)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.reconstruction import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    diagnostics as _recon_diag,
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
    partial_pipeline: dict[str, Any] | None,
    preview_schema_version: int | None,
    reconstruction_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    """Assemble the copy-preview behavior artifact root dict (stable key set)."""

    now = _generated_utc_now()
    events = list(pass1_replay_events)
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
        "notes": {"decode_failed": True},
    }


__all__ = [
    "assemble_copy_preview_behavior_document",
    "build_decode_failure_behavior_document",
    "decode_trace_to_public_dict",
    "pass1_replay_events_shallow_copy",
    "preview_frames_thin_for_behavior_artifact",
    "try_step_1_diagnosis_for_empty_mineable",
]
