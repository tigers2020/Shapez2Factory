"""copy-preview v2 behavior artifact (output-only; not solver / Replay / Debug NDJSON input)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_json import (
    to_jsonable,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    diagnostics as _recon_diag,
)
from django_apps.shapez_core.services.shapez_copy_decode import DecodeTraceResult


@dataclass
class BehaviorArtifactCollector:
    """Accumulates fields for one request-scoped behavior artifact JSON document."""

    input_digest_prefix: str
    _decode_trace: dict[str, Any] | None = None
    _step_0_5: dict[str, Any] | None = None
    _step_1: Any = None
    _reconstruction_summary: dict[str, Any] | None = None
    _step_1_diagnosis: Any = None
    _step_1_diagnosis_error: str | None = None
    _preview_frames: list[dict[str, Any]] = field(default_factory=list)
    _pass1_replay_events: list[dict[str, Any]] = field(default_factory=list)
    _partial_pipeline: dict[str, Any] | None = None
    _preview_schema_version: int | None = None

    def record_decode_trace(self, trace: DecodeTraceResult) -> None:
        self._decode_trace = {
            "steps": list(trace.steps),
            "success": trace.success,
            "error": trace.error,
        }

    def record_copy_preview_pipeline(
        self,
        *,
        existing_layout_analysis: dict[str, Any],
        reconstruction: Any,
        reconstruction_summary: dict[str, Any],
        preview_frames: list[dict[str, Any]],
        pass1_replay_events: list[dict[str, Any]],
        decoded_for_diagnosis: dict[str, Any],
        reconstruction_dto: ReconstructionDTO,
        partial_pipeline: dict[str, Any],
        preview_schema_version: int,
    ) -> None:
        self._step_0_5 = existing_layout_analysis
        self._step_1 = reconstruction
        self._reconstruction_summary = reconstruction_summary
        self._partial_pipeline = partial_pipeline
        self._preview_schema_version = preview_schema_version
        self._preview_frames = [
            {"id": fr.get("id"), "summary": fr.get("summary")}
            for fr in preview_frames
            if isinstance(fr, dict)
        ]
        self._pass1_replay_events = [dict(e) for e in pass1_replay_events]

        if len(reconstruction_dto.mineable_placement_cells) == 0:
            try:
                dto = _recon_diag.diagnose_reconstruction_mineable_empty(
                    decoded_for_diagnosis,
                    reconstruction=reconstruction_dto,
                )
                self._step_1_diagnosis = to_jsonable(dto)
            except Exception as exc:  # noqa: BLE001 — diagnostics are observability-only
                self._step_1_diagnosis_error = f"{type(exc).__name__}:{exc}"

    def build_document(self) -> dict[str, Any]:
        """JSON-serializable root object (required contract keys)."""

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        events = list(self._pass1_replay_events)
        doc: dict[str, Any] = {
            "schema_version": "v2.copy_preview_behavior_artifact.1",
            "artifact_kind": "copy_preview_behavior",
            "generated_utc": now,
            "algorithm_input": False,
            "http_response_included": False,
            "includes_mining_map": False,
            "includes_full_pass1_events": True,
            "source": {
                "view": "copy_preview",
                "engine": "asteroid_mining_layout_v2",
                "pipeline_scope": "decode_to_pass1_preview",
            },
            "input_digest_prefix": self.input_digest_prefix,
            "decode_trace": self._decode_trace or {"steps": [], "success": False, "error": None},
            "step_0_5": self._step_0_5,
            "step_1": self._step_1,
            "step_1_diagnosis": self._step_1_diagnosis,
            "step_1_diagnosis_error": self._step_1_diagnosis_error,
            "preview_frames": self._preview_frames,
            "pass1_replay_events": events,
            "pass1_replay_event_count": len(events),
            "pass1_replay_events_truncated": False,
            "notes": {
                "partial_pipeline": self._partial_pipeline,
                "preview_schema_version": self._preview_schema_version,
                "reconstruction_summary": self._reconstruction_summary,
            },
        }
        return doc


def build_decode_failure_behavior_document(
    *,
    trace: DecodeTraceResult,
    input_digest_prefix: str,
) -> dict[str, Any]:
    """Minimal artifact when decode fails (output-only; no blueprint JSON)."""

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "v2.copy_preview_behavior_artifact.1",
        "artifact_kind": "copy_preview_behavior",
        "generated_utc": now,
        "algorithm_input": False,
        "http_response_included": False,
        "includes_mining_map": False,
        "includes_full_pass1_events": True,
        "source": {
            "view": "copy_preview",
            "engine": "asteroid_mining_layout_v2",
            "pipeline_scope": "decode_to_pass1_preview",
        },
        "input_digest_prefix": input_digest_prefix,
        "decode_trace": {
            "steps": list(trace.steps),
            "success": trace.success,
            "error": trace.error,
        },
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
    "BehaviorArtifactCollector",
    "build_decode_failure_behavior_document",
]
