from __future__ import annotations

from django.test import override_settings

from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    LAB_REPLAY_PAYLOAD_VERSION,
    build_lab_replay_lazy_handle,
    lab_replay_manifest_json_dict,
    lab_replay_payload_mode,
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
