"""Viewer-only: enrich artifact replay_core + complete_map into Lab timeline JSON (BA-4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django_apps.asteroid_lab.models import SolverRun
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
from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import parse_complete_map

_LAYER_EVENT_TYPE: dict[str, ReplayEventType] = {
    "layer_02_exterior_transport": ReplayEventType.EXTERIOR_TRANSPORT_COMPLETED,
    "layer_03_rim_greedy_placement": ReplayEventType.LAYER03_RIM_GREEDY_COMPLETE,
    "layer_05_inner_pattern_fill": ReplayEventType.PATTERN_GENERATED,
    "layer_06_commit_validate": ReplayEventType.VALIDATION_COMPLETED,
}

_LAYER_PHASE: dict[str, ReplayPhase] = {
    "layer_02_exterior_transport": ReplayPhase.ROUTE_PROBE,
    "layer_03_rim_greedy_placement": ReplayPhase.INCREMENTAL_COMMIT,
    "layer_05_inner_pattern_fill": ReplayPhase.PATTERN_GENERATION,
    "layer_06_commit_validate": ReplayPhase.VALIDATION,
}


def lab_replay_frames_are_renderable(frames: list[dict[str, Any]]) -> bool:
    """True when frames carry a Lab ``map_view`` (not raw replay_core records)."""

    if not frames:
        return False
    first = frames[0]
    map_view = first.get("map_view") if isinstance(first, dict) else None
    if not isinstance(map_view, dict):
        return False
    return bool(map_view.get("full_cells") or map_view.get("base_ref"))


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


def compose_lab_replay_frames_from_artifact_run(run: SolverRun) -> list[dict[str, Any]] | None:
    """Build renderable Lab frames from indexed artifact files; never algorithm input."""

    artifact_root = str(run.artifact_root or "").strip()
    if not artifact_root:
        return None
    root = Path(artifact_root)
    try:
        manifest = read_verified_artifact_manifest(root)
    except ArtifactManifestReadError:
        return None
    complete_map_path = _manifest_path(root, manifest, "layer01_complete_map")
    replay_core_path = _manifest_path(root, manifest, "replay_core")
    if complete_map_path is None or replay_core_path is None:
        return None
    if not complete_map_path.is_file() or not replay_core_path.is_file():
        return None
    from django_apps.asteroid_lab.services.artifact_runtime_replay_compose import (
        build_solver_runtime_replay_frames_from_artifact_run,
    )

    runtime_frames = build_solver_runtime_replay_frames_from_artifact_run(run)
    if runtime_frames:
        return runtime_frames

    try:
        complete_map = _load_complete_map(complete_map_path)
        core_records = list(iter_replay_core_frames(replay_core_path))
    except (OSError, json.JSONDecodeError, ValueError, ArtifactReplayLoadError):
        return None
    if not core_records:
        return None

    return [
        replay_timeline_frame_to_json_dict(
            _timeline_frame_from_core_record(record, complete_map=complete_map)
        )
        for record in core_records
    ]


__all__ = [
    "compose_lab_replay_frames_from_artifact_run",
    "lab_replay_frames_are_renderable",
]
