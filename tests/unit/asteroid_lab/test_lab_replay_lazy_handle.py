from __future__ import annotations

from django.test import override_settings

from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    LAB_REPLAY_PAYLOAD_VERSION,
    build_lab_replay_lazy_handle,
    build_lab_replay_lazy_handle_from_summary,
    lab_replay_manifest_json_dict,
    lab_replay_payload_mode,
)
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    build_manifest_summary_from_compose,
)


def test_lab_replay_payload_mode_defaults_lazy() -> None:
    with override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy"):
        assert lab_replay_payload_mode() == "lazy"


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="inline")
def test_build_handle_inline_mode() -> None:
    handle = build_lab_replay_lazy_handle(
        mode="inline",
        frames=[{"frame_index": 0}, {"frame_index": 1}],
        project_slug="demo",
        solver_run_id=42,
    )
    assert handle.mode == "inline"
    assert handle.frame_count == 2
    assert handle.fetch_url is None


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_build_handle_lazy_preview_is_last_frame() -> None:
    frames = [
        {"frame_index": 0, "title": "first"},
        {"frame_index": 1, "title": "last"},
    ]
    handle = build_lab_replay_lazy_handle(
        mode="lazy",
        frames=frames,
        project_slug="demo-slug",
        solver_run_id=99,
    )
    assert handle.mode == "lazy"
    assert handle.frame_count == 2
    assert handle.preview_frame_index == 1
    assert handle.preview_frame == frames[1]
    assert handle.replay_payload_version == LAB_REPLAY_PAYLOAD_VERSION
    assert handle.fetch_url == "/asteroid-miner-layout/p/demo-slug/solver-runs/99/lab-replay/"


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_lab_replay_manifest_json_dict_includes_metrics() -> None:
    frames = [{"frame_index": 0, "title": "a"}, {"frame_index": 1, "title": "b"}]
    handle = build_lab_replay_lazy_handle(
        mode="lazy",
        frames=frames,
        project_slug="demo-slug",
        solver_run_id=99,
    )
    metrics = {"frame_count": 2, "replay_truncated": False}
    manifest = lab_replay_manifest_json_dict(handle=handle, replay_track_metrics=metrics)
    assert manifest["mode"] == "lazy"
    assert manifest["frame_count"] == 2
    assert manifest["preview_frame_index"] == 1
    assert manifest["preview_frame"] == frames[1]
    assert manifest["fetch_url"] == "/asteroid-miner-layout/p/demo-slug/solver-runs/99/lab-replay/"
    assert manifest["replay_track_metrics"] == metrics


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_build_handle_from_summary_lazy_fetch_url_when_frames_present() -> None:
    frames = [{"frame_index": 0}, {"frame_index": 1}]
    metrics = {"frame_count": 2, "replay_truncated": False}
    summary = build_manifest_summary_from_compose(frames=frames, metrics=metrics)
    handle = build_lab_replay_lazy_handle_from_summary(
        project_slug="demo-slug",
        solver_run_id=99,
        manifest_summary=summary,
    )
    assert handle.mode == "lazy"
    assert handle.frame_count == 2
    assert handle.fetch_url == "/asteroid-miner-layout/p/demo-slug/solver-runs/99/lab-replay/"


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_build_handle_from_summary_idle_when_frame_count_zero() -> None:
    summary = build_manifest_summary_from_compose(frames=[], metrics={"frame_count": 0})
    handle = build_lab_replay_lazy_handle_from_summary(
        project_slug="demo-slug",
        solver_run_id=99,
        manifest_summary=summary,
    )
    assert handle.frame_count == 0
    assert handle.fetch_url is None


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_build_handle_from_summary_fetch_url_null_without_run_id() -> None:
    summary = build_manifest_summary_from_compose(
        frames=[{"frame_index": 0}],
        metrics={"frame_count": 1, "replay_truncated": False},
    )
    handle = build_lab_replay_lazy_handle_from_summary(
        project_slug="demo-slug",
        solver_run_id=None,
        manifest_summary=summary,
    )
    assert handle.fetch_url is None


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_build_handle_from_summary_malformed_preview_becomes_null() -> None:
    summary = {
        "replay_payload_version": 1,
        "lab_replay_cache_schema_version": 1,
        "frame_count": 1,
        "preview_frame_index": 0,
        "preview_frame": "not-a-dict",
        "replay_track_metrics": {"frame_count": 1},
    }
    handle = build_lab_replay_lazy_handle_from_summary(
        project_slug="demo-slug",
        solver_run_id=42,
        manifest_summary=summary,
    )
    assert handle.preview_frame is None


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_build_handle_from_summary_uses_replay_payload_version_from_summary() -> None:
    summary = build_manifest_summary_from_compose(
        frames=[{"frame_index": 0}],
        metrics={"frame_count": 1, "replay_truncated": False},
    )
    summary["replay_payload_version"] = 2
    handle = build_lab_replay_lazy_handle_from_summary(
        project_slug="demo-slug",
        solver_run_id=1,
        manifest_summary=summary,
    )
    assert handle.replay_payload_version == 2


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_manifest_json_dict_from_summary_handle() -> None:
    frames = [{"frame_index": 0, "title": "only"}]
    metrics = {"frame_count": 1, "replay_truncated": False}
    summary = build_manifest_summary_from_compose(frames=frames, metrics=metrics)
    handle = build_lab_replay_lazy_handle_from_summary(
        project_slug="proj-x",
        solver_run_id=7,
        manifest_summary=summary,
    )
    manifest = lab_replay_manifest_json_dict(
        handle=handle,
        replay_track_metrics=dict(summary["replay_track_metrics"]),
    )
    assert manifest["mode"] == "lazy"
    assert manifest["frame_count"] == 1
    assert manifest["preview_frame"] == frames[0]
    assert manifest["fetch_url"] == "/asteroid-miner-layout/p/proj-x/solver-runs/7/lab-replay/"
    assert manifest["replay_track_metrics"] == metrics
