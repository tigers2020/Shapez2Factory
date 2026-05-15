"""Public copy-preview behavior artifact schema constants (JSON output contract).

Not imported by domain / placement / routing / validation (see unit boundary tests).
"""

from __future__ import annotations

from typing import Any

COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION = "v2.copy_preview_behavior_artifact.2"
ARTIFACT_KIND_COPY_PREVIEW_BEHAVIOR = "copy_preview_behavior"

# Top-level keys required on every copy-preview behavior artifact document (stable contract).
COPY_PREVIEW_BEHAVIOR_DOCUMENT_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "generated_utc",
        "algorithm_input",
        "http_response_included",
        "includes_mining_map",
        "includes_full_pass1_events",
        "source",
        "input_digest_prefix",
        "decode_trace",
        "step_0_5",
        "step_1",
        "step_1_diagnosis",
        "step_1_diagnosis_error",
        "preview_frames",
        "pass1_replay_events",
        "pass1_replay_event_count",
        "pass1_replay_events_truncated",
        "runtime_trace_events",
        "runtime_trace_event_count",
        "runtime_trace_events_truncated",
        "notes",
    }
)


def copy_preview_behavior_source_dict() -> dict[str, Any]:
    """``source`` object embedded in copy-preview behavior artifacts."""

    return {
        "view": "copy_preview",
        "engine": "asteroid_mining_layout_v2",
        "pipeline_scope": "decode_to_pass1_preview",
    }


__all__ = [
    "ARTIFACT_KIND_COPY_PREVIEW_BEHAVIOR",
    "COPY_PREVIEW_BEHAVIOR_DOCUMENT_REQUIRED_KEYS",
    "COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION",
    "copy_preview_behavior_source_dict",
]
