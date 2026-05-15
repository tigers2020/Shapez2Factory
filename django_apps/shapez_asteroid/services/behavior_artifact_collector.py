"""copy-preview v2 behavior artifact (output-only; not solver / Replay / Debug NDJSON input)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization import (
    dto_adapters,
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
    _runtime_trace_events: list[dict[str, Any]] = field(default_factory=list)
    _runtime_trace_events_truncated: bool = False

    def record_decode_trace(self, trace: DecodeTraceResult) -> None:
        self._decode_trace = dto_adapters.decode_trace_to_public_dict(trace)

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
        runtime_trace: TraceCollector | None = None,
    ) -> None:
        self._step_0_5 = existing_layout_analysis
        self._step_1 = reconstruction
        self._reconstruction_summary = reconstruction_summary
        self._partial_pipeline = partial_pipeline
        self._preview_schema_version = preview_schema_version
        self._preview_frames = dto_adapters.preview_frames_thin_for_behavior_artifact(
            preview_frames
        )
        self._pass1_replay_events = dto_adapters.pass1_replay_events_shallow_copy(
            pass1_replay_events
        )
        if runtime_trace is not None:
            self._runtime_trace_events, self._runtime_trace_events_truncated = (
                dto_adapters.runtime_trace_events_for_behavior_artifact(runtime_trace.events)
            )
        else:
            self._runtime_trace_events = []
            self._runtime_trace_events_truncated = False

        if len(reconstruction_dto.mineable_placement_cells) == 0:
            self._step_1_diagnosis, self._step_1_diagnosis_error = (
                dto_adapters.try_step_1_diagnosis_for_empty_mineable(
                    decoded_for_diagnosis,
                    reconstruction_dto,
                )
            )

    def build_document(self) -> dict[str, Any]:
        """JSON-serializable root object (required contract keys)."""

        return dto_adapters.assemble_copy_preview_behavior_document(
            input_digest_prefix=self.input_digest_prefix,
            decode_trace=self._decode_trace or {"steps": [], "success": False, "error": None},
            step_0_5=self._step_0_5,
            step_1=self._step_1,
            step_1_diagnosis=self._step_1_diagnosis,
            step_1_diagnosis_error=self._step_1_diagnosis_error,
            preview_frames_thin=self._preview_frames,
            pass1_replay_events=self._pass1_replay_events,
            runtime_trace_events=self._runtime_trace_events,
            runtime_trace_events_truncated=self._runtime_trace_events_truncated,
            partial_pipeline=self._partial_pipeline,
            preview_schema_version=self._preview_schema_version,
            reconstruction_summary=self._reconstruction_summary,
        )


build_decode_failure_behavior_document = dto_adapters.build_decode_failure_behavior_document

__all__ = [
    "BehaviorArtifactCollector",
    "build_decode_failure_behavior_document",
]
