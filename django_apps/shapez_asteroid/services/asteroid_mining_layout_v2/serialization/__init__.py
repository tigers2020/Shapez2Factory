"""Public JSON and artifact adapters (no solver algorithm input)."""

from .dto_adapters import (
    assemble_copy_preview_behavior_document,
    build_decode_failure_behavior_document,
    decode_trace_to_public_dict,
    pass1_replay_events_shallow_copy,
    preview_frames_thin_for_behavior_artifact,
    try_step_1_diagnosis_for_empty_mineable,
)
from .json_safe import existing_layout_analysis_to_json, to_jsonable
from .public_artifacts import (
    ARTIFACT_KIND_COPY_PREVIEW_BEHAVIOR,
    COPY_PREVIEW_BEHAVIOR_DOCUMENT_REQUIRED_KEYS,
    COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION,
    copy_preview_behavior_source_dict,
)

__all__ = [
    "ARTIFACT_KIND_COPY_PREVIEW_BEHAVIOR",
    "assemble_copy_preview_behavior_document",
    "build_decode_failure_behavior_document",
    "COPY_PREVIEW_BEHAVIOR_DOCUMENT_REQUIRED_KEYS",
    "COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION",
    "copy_preview_behavior_source_dict",
    "decode_trace_to_public_dict",
    "existing_layout_analysis_to_json",
    "pass1_replay_events_shallow_copy",
    "preview_frames_thin_for_behavior_artifact",
    "to_jsonable",
    "try_step_1_diagnosis_for_empty_mineable",
]
