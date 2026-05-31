"""Viewer-only: rebuild L2/L3 solver runtime replay frames from a CLI artifact (output-only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django_apps.asteroid_lab.models import SolverRun
from django_apps.asteroid_lab.replay.layer02_segment import map_view_from_complete_map
from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
    build_solver_runtime_replay_frames,
)
from django_apps.asteroid_lab.replay.timeline_serialization import replay_map_view_to_json_dict
from django_apps.asteroid_lab.services.artifact_manifest_reader import (
    ArtifactManifestReadError,
    ArtifactManifestRecord,
    read_verified_artifact_manifest,
)
from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
    _load_complete_map,
    _manifest_path,
)
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    execute_layer_02_exterior_transport_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.application.asteroid_lab.reconstruction_capacity import (
    build_terrain_capacity_summary_row,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def _capacity_envelope(
    *,
    complete_map: ReconstructionCompleteMap,
    rules: GameDataRulesPort,
) -> dict[str, Any]:
    shape_count = int(complete_map.shape_field_cell_count)
    fluid_count = int(complete_map.fluid_field_cell_count)
    primary = "shape" if shape_count >= fluid_count else "fluid"

    def _row(resource_kind: str, platform_count: int) -> dict[str, Any]:
        rule = rules.mining_extraction_rule(resource_kind=resource_kind)
        return build_terrain_capacity_summary_row(
            resource_kind=resource_kind,
            platform_count=platform_count,
            mini_unit_output_per_min=rule.mini_unit_output_per_min,
            output_unit=rule.output_unit,
            max_extension_count=rule.max_extension_count,
            source_kind=rule.source_kind,
            authority="game_data_snapshot",
        )

    return {
        "capacity_basis": "terrain_upper_bound",
        "primary_resource_kind": primary,
        "confirmed_platforms_by_resource": {
            "shape": shape_count,
            "fluid": fluid_count,
        },
        "by_resource": {
            "shape": _row("shape", shape_count),
            "fluid": _row("fluid", fluid_count),
        },
    }


def _load_solver_summary(root: Path, manifest: ArtifactManifestRecord) -> dict[str, Any]:
    summary_path = _manifest_path(root, manifest, "solver_summary")
    if summary_path is None or not summary_path.is_file():
        return {}
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _load_genetic_sample_seeds(
    root: Path,
    manifest: ArtifactManifestRecord,
) -> GeneticSampleSeedSnapshot | None:
    seeds_path = _manifest_path(root, manifest, "genetic_sample_seeds")
    if seeds_path is None or not seeds_path.is_file():
        return None
    payload = json.loads(seeds_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return GeneticSampleSeedSnapshot.from_payload(payload)


def build_solver_runtime_replay_frames_from_artifact_run(
    run: SolverRun,
) -> list[dict[str, Any]] | None:
    """Re-execute L2/L3 on artifact inputs and emit overlay-capable runtime replay frames."""

    artifact_root = str(run.artifact_root or "").strip()
    if not artifact_root:
        return None
    root = Path(artifact_root)
    try:
        manifest = read_verified_artifact_manifest(root)
    except ArtifactManifestReadError:
        return None

    complete_map_path = _manifest_path(root, manifest, "layer01_complete_map")
    snapshot_path = _manifest_path(root, manifest, "game_data_snapshot")
    if complete_map_path is None or snapshot_path is None:
        return None
    if not complete_map_path.is_file() or not snapshot_path.is_file():
        return None

    try:
        complete_map = _load_complete_map(complete_map_path)
        snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if not isinstance(snapshot_payload, dict):
            return None
        rules = JsonSnapshotGameDataRulesAdapter.from_payload(snapshot_payload)
        genetic_sample_seeds = _load_genetic_sample_seeds(root, manifest)
        solver_summary = _load_solver_summary(root, manifest)
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None

    throughput_target_percent = int(solver_summary.get("throughput_target_percent") or 80)
    capacity_envelope = _capacity_envelope(complete_map=complete_map, rules=rules)
    exterior_plan = execute_layer_02_exterior_transport_plan(
        complete_map=complete_map,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=throughput_target_percent,
        rules=rules,
    )
    plan_wire = exterior_connector_plan_to_metrics_dict(exterior_plan).get(
        "exterior_connector_plan"
    )
    if not isinstance(plan_wire, dict):
        return None

    layer03 = run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=genetic_sample_seeds,
    )

    lab_source = [
        {
            "map_view": replay_map_view_to_json_dict(
                map_view_from_complete_map(complete_map),
            ),
        },
    ]

    return build_solver_runtime_replay_frames(
        complete_map=complete_map,
        lab_frames_before_append=lab_source,
        exterior_plan_wire=plan_wire,
        layer03=layer03,
        layer04=None,
    )


__all__ = ["build_solver_runtime_replay_frames_from_artifact_run"]
