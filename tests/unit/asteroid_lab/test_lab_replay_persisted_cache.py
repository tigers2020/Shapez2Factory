"""Unit tests for artifact-first composed replay cache loading."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.db.models.fields.json import KeyTransform

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
    build_manifest_summary_from_compose,
    is_cache_summary_valid,
    load_composed_frames_for_run_id,
    load_manifest_summary_for_run_id,
    persist_composed_replay_for_run_id,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
    SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY,
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)


@pytest.fixture
def cache_project() -> m.AsteroidProject:
    return m.AsteroidProject.objects.create(name="Cache proj", slug="cache-proj-13c2")


@pytest.mark.django_db
def test_build_manifest_summary_includes_cache_schema_version() -> None:
    frames = [{"frame_index": 0, "title": "a"}, {"frame_index": 1, "title": "b"}]
    metrics = {"frame_count": 2, "replay_truncated": False}
    summary = build_manifest_summary_from_compose(frames=frames, metrics=metrics)
    assert summary["lab_replay_cache_schema_version"] == CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION
    assert summary["replay_payload_version"] == 1
    assert summary["frame_count"] == 2
    assert summary["preview_frame_index"] == 1
    assert summary["preview_frame"] == frames[1]
    assert summary["replay_track_metrics"] == metrics


def test_is_cache_summary_valid_rejects_wrong_schema() -> None:
    assert is_cache_summary_valid({"lab_replay_cache_schema_version": 0}) is False
    assert is_cache_summary_valid(None) is False
    assert (
        is_cache_summary_valid(
            {
                "lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
                "frame_count": 1,
            }
        )
        is True
    )
    assert (
        is_cache_summary_valid(
            {
                "mode": "artifact_jsonl",
                "replay_core_path": "F:/tmp/replay_core.jsonl",
            }
        )
        is True
    )


@pytest.mark.django_db
def test_persist_preserves_unrelated_config_json_keys(cache_project: m.AsteroidProject) -> None:
    run = m.SolverRun.objects.create(
        project=cache_project,
        run_key="rk-cache-1",
        config_json={
            SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY: [{"event_type": "layer02_complete"}],
            SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {"completed_layer_slugs": ["layer_01"]},
        },
    )
    frames = [{"frame_index": 0, "full_map": []}]
    metrics = {"frame_count": 1, "replay_truncated": False}
    persist_composed_replay_for_run_id(int(run.pk), frames=frames, metrics=metrics)
    run.refresh_from_db()
    config = dict(run.config_json or {})
    runtime_frames = config[SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY]
    assert runtime_frames == [{"event_type": "layer02_complete"}]
    assert config[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] == {"completed_layer_slugs": ["layer_01"]}
    assert config[SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY] == frames
    assert is_cache_summary_valid(config[SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY])


@pytest.mark.django_db
def test_load_composed_frames_and_manifest_round_trip(cache_project: m.AsteroidProject) -> None:
    run = m.SolverRun.objects.create(project=cache_project, run_key="rk-cache-2", config_json={})
    frames = [{"frame_index": 0}, {"frame_index": 1}]
    metrics = {"frame_count": 2, "replay_truncated": False}
    persist_composed_replay_for_run_id(int(run.pk), frames=frames, metrics=metrics)
    loaded_frames = load_composed_frames_for_run_id(int(run.pk))
    summary = load_manifest_summary_for_run_id(int(run.pk))
    assert loaded_frames == frames
    assert is_cache_summary_valid(summary)
    assert summary is not None
    assert summary["frame_count"] == 2


@pytest.mark.django_db
def test_load_manifest_summary_uses_key_transform_not_full_config(
    cache_project: m.AsteroidProject,
) -> None:
    """Manifest loader must not materialize full config_json (§4.7)."""
    summary_seed = build_manifest_summary_from_compose(
        frames=[{"frame_index": 0}],
        metrics={"frame_count": 1, "replay_truncated": False},
    )
    run = m.SolverRun.objects.create(
        project=cache_project,
        run_key="rk-cache-3",
        config_json={
            SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY: summary_seed,
            SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY: [
                {"frame_index": i} for i in range(5000)
            ],
        },
    )
    sentinel = MagicMock()
    original_filter = m.SolverRun.objects.filter

    def filter_with_sentinel(*args: object, **kwargs: object) -> MagicMock:
        qs = original_filter(*args, **kwargs)
        sentinel.filter_called = True
        original_values_list = qs.values_list

        def values_list(*vl_args: object, **vl_kwargs: object) -> object:
            if vl_args and isinstance(vl_args[0], KeyTransform):
                kt = vl_args[0]
                assert kt.key_name == SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY
            return original_values_list(*vl_args, **vl_kwargs)

        qs.values_list = values_list  # type: ignore[method-assign]
        return qs

    with patch.object(m.SolverRun.objects, "filter", side_effect=filter_with_sentinel):
        loaded = load_manifest_summary_for_run_id(int(run.pk))
    assert loaded is not None
    assert loaded["frame_count"] == 1
    assert sentinel.filter_called is True


@pytest.mark.django_db
def test_load_manifest_summary_does_not_call_composed_frames_loader(
    cache_project: m.AsteroidProject,
) -> None:
    run = m.SolverRun.objects.create(
        project=cache_project,
        run_key="rk-cache-4",
        config_json={
            SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY: build_manifest_summary_from_compose(
                frames=[{"frame_index": 0}],
                metrics={"frame_count": 1, "replay_truncated": False},
            ),
        },
    )
    with patch(
        "django_apps.asteroid_lab.services.lab_replay_persisted_cache.load_composed_frames_for_run_id",
        side_effect=AssertionError("composed frames loader must not run"),
    ):
        summary = load_manifest_summary_for_run_id(int(run.pk))
    assert summary is not None
    assert summary["frame_count"] == 1
