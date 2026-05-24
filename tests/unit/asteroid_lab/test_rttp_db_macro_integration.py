"""PR-I: DB :rttp macro-only persist/read and run_config wiring."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.replay_sink import DbRttpReplaySink
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    _metrics_from_row,
    replay_frame_to_optimization_milestone_json,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    _rttp_pipeline_config_from_run_config,
)
from tests.support.macro_triple_greenfield_fixture import build_macro_triple_greenfield_input

pytestmark = pytest.mark.django_db


@pytest.fixture
def replay_track() -> m.ReplayTrack:
    project = m.AsteroidProject.objects.create(name="MacroDb", slug="macro-db-proj")
    return m.ReplayTrack.objects.create(project=project, track_key="macro-db-track")


def _frames_by_event_type(track_id: int) -> dict[str, m.ReplayFrame]:
    out: dict[str, m.ReplayFrame] = {}
    rows = m.ReplayFrame.objects.filter(replay_track_id=track_id).order_by("frame_index")
    for row in rows:
        payload = dict(row.frame_payload or {})
        event_type = str(payload.get("event_type") or "")
        if event_type:
            out[event_type] = row
    return out


def _overlay_kinds(frame: m.ReplayFrame) -> set[str]:
    overlay = dict(frame.cell_overlay_json or {})
    cells = overlay.get("cells") or []
    return {str(c.get("kind")) for c in cells if isinstance(c, dict)}


def test_run_config_maps_macro_only_to_pipeline_config() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {
            SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: True,
            SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY: 32,
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": False},
        }
    )
    assert cfg.macro_only_mode is True
    assert cfg.max_macro_candidates == 32
    assert cfg.deferred_retry_shadow.enabled is False

    default_cfg = _rttp_pipeline_config_from_run_config({})
    assert default_cfg.macro_only_mode is False
    assert default_cfg.max_macro_candidates == 64
    assert default_cfg.deferred_retry_shadow.enabled is True


def test_db_persist_macro_candidate_pool_and_commit_metrics(
    replay_track: m.ReplayTrack,
) -> None:
    inp = build_macro_triple_greenfield_input()
    sink = DbRttpReplaySink(replay_track.id)
    run_rttp_pipeline(
        inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(macro_only_mode=True),
        replay_sink=sink,
    )

    by_type = _frames_by_event_type(replay_track.id)
    assert set(by_type) >= {
        et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
        et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
        et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
        et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT,
    }

    candidate = by_type[et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT]
    cand_metrics = _metrics_from_row(candidate)
    assert cand_metrics.get("macro_normal_count", 0) >= 1
    assert cand_metrics.get("child_normal_count", 0) >= 3
    assert "macro.combined_footprint" in _overlay_kinds(candidate)

    commit = by_type[et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT]
    assert "macro.shared_lift" in _overlay_kinds(commit)

    selection = by_type[et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT]
    order = list(selection.metric_snapshot_json.get("commit_order") or [])
    assert order
    assert all(len(slot_id) == 64 for slot_id in order)

    commit_metrics = _metrics_from_row(commit)
    macro_ids = commit_metrics.get("committed_macro_ids") or []
    child_ids = commit_metrics.get("committed_child_ids") or []
    assert macro_ids
    assert child_ids
    assert len(child_ids) >= 3


def test_db_v01_candidate_pool_metrics_without_macro_keys(
    replay_track: m.ReplayTrack,
    greenfield_optimization_input,
) -> None:
    sink = DbRttpReplaySink(replay_track.id)
    run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(macro_only_mode=False),
        replay_sink=sink,
    )

    by_type = _frames_by_event_type(replay_track.id)
    candidate = by_type[et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT]
    metrics = _metrics_from_row(candidate)
    assert "macro_normal_count" not in metrics
    assert "child_normal_count" not in metrics

    commit = by_type[et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT]
    commit_metrics = _metrics_from_row(commit)
    assert "committed_macro_ids" not in commit_metrics
    assert "committed_child_ids" not in commit_metrics

    selection = by_type[et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT]
    order = list(selection.metric_snapshot_json.get("commit_order") or [])
    assert order
    assert all(len(slot_id) != 64 for slot_id in order)


def test_milestone_payload_reads_persisted_macro_metrics(
    replay_track: m.ReplayTrack,
) -> None:
    inp = build_macro_triple_greenfield_input()
    sink = DbRttpReplaySink(replay_track.id)
    run_rttp_pipeline(
        inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(macro_only_mode=True),
        replay_sink=sink,
    )

    commit = _frames_by_event_type(replay_track.id)[et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT]
    milestone = replay_frame_to_optimization_milestone_json(commit)
    assert milestone is not None
    metrics = milestone["metrics"]
    assert metrics.get("committed_macro_ids")
    assert metrics.get("committed_child_ids")
    assert metrics.get("validation_passed") is True
