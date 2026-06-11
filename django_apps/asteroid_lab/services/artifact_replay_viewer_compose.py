"""Viewer-only: enrich artifact replay_core + complete_map into Lab timeline JSON (BA-4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django_apps.asteroid_lab.models import SolverRun
from django_apps.asteroid_lab.observability.lab_perf_trace import perf_span
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.layer02_segment import map_view_from_complete_map
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayTimelineFrame
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_timeline_frame_to_json_dict,
)
from django_apps.asteroid_lab.services.artifact_manifest_reader import (
    ArtifactManifestReadError,
    ArtifactManifestRecord,
    read_verified_artifact_manifest,
)
from django_apps.asteroid_lab.services.artifact_replay_loader import (
    ArtifactReplayLoadError,
    iter_replay_core_frames,
)
from django_apps.asteroid_lab.services.lab_replay_diagnostics import (
    diagnostic_severity_for_reason,
)
from django_apps.asteroid_lab.services.runtime_wire_compose import (
    compose_lab_replay_frames_from_runtime_wires,
    load_and_validate_runtime_wires,
    wire_content_hash_from_document,
)
from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import parse_complete_map

_LAYER_EVENT_TYPE: dict[str, ReplayEventType] = {
    "layer_02_exterior_transport": ReplayEventType.EXTERIOR_TRANSPORT_COMPLETED,
    "layer_03_rim_greedy_placement": ReplayEventType.LAYER03_RIM_GREEDY_COMPLETE,
    "layer_04_inner_pattern_fill": ReplayEventType.PATTERN_GENERATED,
    "layer_05_inner_pattern_fill": ReplayEventType.PATTERN_GENERATED,
    "layer_05_transport_routing": ReplayEventType.LAYER05_TRANSPORT_ROUTING_COMPLETE,
    "layer_04_transport_routing": ReplayEventType.LAYER04_TRANSPORT_ROUTING_COMPLETE,
    "layer_06_commit_validate": ReplayEventType.VALIDATION_COMPLETED,
}

_LAYER_PHASE: dict[str, ReplayPhase] = {
    "layer_02_exterior_transport": ReplayPhase.ROUTE_PROBE,
    "layer_03_rim_greedy_placement": ReplayPhase.INCREMENTAL_COMMIT,
    "layer_04_inner_pattern_fill": ReplayPhase.PATTERN_GENERATION,
    "layer_05_inner_pattern_fill": ReplayPhase.PATTERN_GENERATION,
    "layer_05_transport_routing": ReplayPhase.ROUTE_PROBE,
    "layer_04_transport_routing": ReplayPhase.ROUTE_PROBE,
    "layer_06_commit_validate": ReplayPhase.VALIDATION,
}

REPLAY_COMPOSE_META_INSPECTOR_KEY = "replay_compose_meta"


def lab_replay_frames_are_renderable(frames: list[dict[str, Any]]) -> bool:
    """True when frames carry a Lab ``map_view`` (not raw replay_core records)."""

    if not frames:
        return False
    first = frames[0]
    map_view = first.get("map_view") if isinstance(first, dict) else None
    if not isinstance(map_view, dict):
        return False
    return bool(map_view.get("full_cells") or map_view.get("base_ref"))


def extract_replay_compose_meta(frames: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not frames:
        return None
    inspector = frames[0].get("inspector")
    if not isinstance(inspector, dict):
        return None
    meta = inspector.get(REPLAY_COMPOSE_META_INSPECTOR_KEY)
    return dict(meta) if isinstance(meta, dict) else None


def _manifest_path(
    artifact_dir: Path,
    manifest: ArtifactManifestRecord,
    key: str,
) -> Path | None:
    relpath = manifest.paths.get(key)
    if not relpath:
        return None
    root = artifact_dir.resolve()
    path = (root / str(relpath)).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def _load_complete_map(path: Path) -> ReconstructionCompleteMap:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"complete_map payload must be object: {path}"
        raise ValueError(msg)
    return parse_complete_map(payload)


def _timeline_frame_from_core_record(
    record: dict[str, Any],
    *,
    complete_map: ReconstructionCompleteMap,
) -> ReplayTimelineFrame:
    layer_slug = str(record.get("layer_slug") or "solver.layer")
    event_type = _LAYER_EVENT_TYPE.get(layer_slug, ReplayEventType.RESULT_LAYOUT)
    phase = _LAYER_PHASE.get(layer_slug, ReplayPhase.INCREMENTAL_COMMIT)
    elapsed_ms = record.get("elapsed_ms")
    metrics: dict[str, Any] = {}
    if isinstance(elapsed_ms, int):
        metrics["elapsed_ms"] = elapsed_ms
    outcome = record.get("outcome")
    if isinstance(outcome, str) and outcome:
        metrics["layer_outcome"] = outcome
    return ReplayTimelineFrame(
        frame_index=int(record["frame_index"]),
        phase=phase,
        event_type=event_type,
        title=layer_slug,
        description=str(record.get("event") or "layer_done"),
        map_view=map_view_from_complete_map(complete_map),
        inspector={"layer_slug": layer_slug, "replay_source": "artifact_replay_core"},
        metrics=metrics,
    )


def _stamp_degraded_compose_meta(
    frames: list[dict[str, Any]],
    *,
    diagnostic_reason: str | None,
) -> None:
    if not frames:
        return
    severity = diagnostic_severity_for_reason(diagnostic_reason)
    inspector = frames[0].setdefault("inspector", {})
    if isinstance(inspector, dict):
        inspector[REPLAY_COMPOSE_META_INSPECTOR_KEY] = {
            "diagnostic_reason": diagnostic_reason,
            "diagnostic_severity": severity,
            "replay_projection_mode": "degraded_terrain",
            "algorithm_rerun_count": 0,
        }


def _compose_degraded_terrain_frames(
    complete_map: ReconstructionCompleteMap,
    *,
    replay_core_records: list[dict[str, Any]] | None,
    diagnostic_reason: str | None,
) -> list[dict[str, Any]] | None:
    if replay_core_records:
        frames = [
            replay_timeline_frame_to_json_dict(
                _timeline_frame_from_core_record(record, complete_map=complete_map)
            )
            for record in replay_core_records
        ]
        _stamp_degraded_compose_meta(frames, diagnostic_reason=diagnostic_reason)
        return frames

    frame = replay_timeline_frame_to_json_dict(
        ReplayTimelineFrame(
            frame_index=0,
            phase=ReplayPhase.INCREMENTAL_COMMIT,
            event_type=ReplayEventType.RESULT_LAYOUT,
            title="complete_map",
            description="terrain_only",
            map_view=map_view_from_complete_map(complete_map),
            inspector={"replay_source": "artifact_complete_map_only"},
            metrics={},
        )
    )
    frames = [frame]
    _stamp_degraded_compose_meta(frames, diagnostic_reason=diagnostic_reason)
    return frames


def compose_lab_replay_frames_from_artifact_run(run: SolverRun) -> list[dict[str, Any]] | None:
    """Build renderable Lab frames from indexed artifact files; never algorithm input."""

    artifact_root = str(run.artifact_root or "").strip()
    if not artifact_root:
        return None
    root = Path(artifact_root)
    manifest = None
    complete_map_path = None
    replay_core_path = None
    with perf_span("artifact_manifest_load_ms"):
        try:
            manifest = read_verified_artifact_manifest(root)
        except ArtifactManifestReadError:
            return None
        complete_map_path = _manifest_path(root, manifest, "layer01_complete_map")
        replay_core_path = _manifest_path(root, manifest, "replay_core")

    if complete_map_path is None or not complete_map_path.is_file():
        return None

    with perf_span("complete_map_load_ms"):
        try:
            complete_map = _load_complete_map(complete_map_path)
        except (OSError, json.JSONDecodeError, ValueError):
            return None

    core_records: list[dict[str, Any]] | None = None
    if replay_core_path is not None and replay_core_path.is_file():
        with perf_span("replay_core_parse_ms"):
            try:
                core_records = list(iter_replay_core_frames(replay_core_path))
            except (OSError, json.JSONDecodeError, ValueError, ArtifactReplayLoadError):
                core_records = None

    with perf_span("runtime_wires_load_ms"):
        wire_result = load_and_validate_runtime_wires(root, manifest)

    if wire_result.ok and wire_result.bundle is not None and wire_result.document is not None:
        with perf_span("runtime_wires_project_ms"):
            frames = compose_lab_replay_frames_from_runtime_wires(
                complete_map=complete_map,
                wires_doc=wire_result.document,
                bundle=wire_result.bundle,
                diagnostic_reason=wire_result.degraded_reason,
                diagnostic_severity=wire_result.diagnostic_severity,
            )
            content_hash = wire_content_hash_from_document(wire_result.document)
            if frames:
                inspector = frames[0].get("inspector")
                if isinstance(inspector, dict):
                    meta = inspector.get(REPLAY_COMPOSE_META_INSPECTOR_KEY)
                    if isinstance(meta, dict) and content_hash is not None:
                        meta["wire_content_hash"] = content_hash
            return frames

    return _compose_degraded_terrain_frames(
        complete_map,
        replay_core_records=core_records if core_records else None,
        diagnostic_reason=wire_result.degraded_reason,
    )


__all__ = [
    "REPLAY_COMPOSE_META_INSPECTOR_KEY",
    "compose_lab_replay_frames_from_artifact_run",
    "extract_replay_compose_meta",
    "lab_replay_frames_are_renderable",
]
