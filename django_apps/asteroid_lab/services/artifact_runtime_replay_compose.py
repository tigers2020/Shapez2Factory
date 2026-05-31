"""Viewer-only: rebuild L2/L3 runtime replay (append overlays) from CLI artifact + summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_GREEDY_PLACEMENT
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.run import (
    execute_layer_02_exterior_transport_plan,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_seed import (
    DEFAULT_GREEDY_SEEDS,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.layer02_segment import map_view_from_complete_map
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
    build_solver_runtime_replay_frames,
)
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayTimelineFrame
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_timeline_frame_to_json_dict,
)
from django_apps.asteroid_lab.services.artifact_manifest_reader import ArtifactManifestRecord
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    GameDataSnapshotInvalid,
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)

_LAYER_SUMMARY_COMPLETED = frozenset({"completed", "superseded"})


def _throughput_target_percent(solver_summary: dict[str, Any]) -> int:
    raw = solver_summary.get("throughput_target_percent")
    if raw is None:
        return 80
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 80


def _layer03_completed_in_summary(solver_summary: dict[str, Any]) -> bool:
    slugs = solver_summary.get("completed_layer_slugs")
    if isinstance(slugs, list) and LAYER_03_RIM_GREEDY_PLACEMENT in slugs:
        return True
    for item in solver_summary.get("layer_summaries") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("layer_slug") or "") != LAYER_03_RIM_GREEDY_PLACEMENT:
            continue
        if str(item.get("outcome") or "") in _LAYER_SUMMARY_COMPLETED:
            return True
    return False


def _reconstruction_source_frame_dict(complete_map: ReconstructionCompleteMap) -> dict[str, Any]:
    map_view = map_view_from_complete_map(complete_map)
    frame = ReplayTimelineFrame(
        frame_index=0,
        phase=ReplayPhase.RECONSTRUCTION,
        event_type=ReplayEventType.RECONSTRUCTION_COMPLETED,
        title="Reconstruction complete",
        description="Artifact complete map (viewer recompose)",
        map_view=map_view,
        inspector={"replay_source": "artifact_runtime_recompose"},
        metrics={},
    )
    return replay_timeline_frame_to_json_dict(frame)


def _load_game_data_rules(snapshot_path: Path) -> JsonSnapshotGameDataRulesAdapter | None:
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, GameDataSnapshotInvalid):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return JsonSnapshotGameDataRulesAdapter.from_payload(payload)
    except (GameDataSnapshotInvalid, ValueError, KeyError):
        return None


def build_runtime_replay_frames_from_artifact(
    *,
    complete_map: ReconstructionCompleteMap,
    solver_summary: dict[str, Any],
    game_data_snapshot_path: Path | None,
) -> list[dict[str, Any]] | None:
    """Re-run L2/L3 (viewer-only) and emit assembler frames with append overlays."""

    rules = None
    if game_data_snapshot_path is not None and game_data_snapshot_path.is_file():
        rules = _load_game_data_rules(game_data_snapshot_path)
    throughput = _throughput_target_percent(solver_summary)
    capacity_envelope = build_reconstruction_capacity_envelope(complete_map=complete_map)

    try:
        exterior_plan = execute_layer_02_exterior_transport_plan(
            complete_map=complete_map,
            capacity_envelope=capacity_envelope,
            throughput_target_percent=throughput,
            speed_tier=1,
            rules=rules,
        )
    except (LookupError, ValueError):
        return None

    plan_metrics = exterior_connector_plan_to_metrics_dict(exterior_plan)
    plan_wire = plan_metrics.get("exterior_connector_plan")
    if not isinstance(plan_wire, dict):
        return None

    layer03 = None
    if _layer03_completed_in_summary(solver_summary):
        layer03 = run_layer_03_rim_greedy_placement(
            complete_map=complete_map,
            exterior_plan=exterior_plan,
            budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
            seed_catalog=DEFAULT_GREEDY_SEEDS,
        )

    source_frame = _reconstruction_source_frame_dict(complete_map)
    return build_solver_runtime_replay_frames(
        complete_map=complete_map,
        lab_frames_before_append=[source_frame],
        exterior_plan_wire=plan_wire,
        layer03=layer03,
        layer04=None,
    )


def game_data_snapshot_path_for_manifest(
    artifact_dir: Path,
    manifest: ArtifactManifestRecord,
) -> Path | None:
    relpath = manifest.paths.get("game_data_snapshot")
    if not relpath:
        return None
    root = artifact_dir.resolve()
    path = (root / str(relpath)).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


__all__ = [
    "build_runtime_replay_frames_from_artifact",
    "game_data_snapshot_path_for_manifest",
]
