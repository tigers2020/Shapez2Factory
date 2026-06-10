"""Lab lazy replay must refresh track metrics (frozen exterior plan)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_apply_loaded_lab_replay_payload_assigns_replay_track_metrics() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "function applyLoadedLabReplayPayload(payload)" in js
    assert "payload.replay_track_metrics" in js
    assert "replayTrackMetrics = payload.replay_track_metrics" in js
    idx = js.find("function applyLoadedLabReplayPayload(payload)")
    body = js[idx : idx + 900]
    assert "mountLabCanvasRenderer();" in body


def test_replace_lab_replay_payload_mounts_canvas_renderer() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    idx = js.find("function replaceLabReplayPayload(payload")
    end = js.find("\n    function syncProjectSlugHiddenFromRedirect", idx)
    body = js[idx:end] if end > idx else js[idx : idx + 4000]
    assert body.count("mountLabCanvasRenderer();") >= 2


def test_lazy_replace_lab_replay_payload_applies_track_metrics_before_early_return() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    idx_lazy = js.find('lazy.mode === "lazy"')
    assert idx_lazy >= 0
    chunk = js[idx_lazy : idx_lazy + 1200]
    assert "replay_track_metrics" in chunk


def test_lazy_replay_prefetches_full_frames_when_preview_is_renderable() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "function scheduleLazyReplayPrefetch()" in js
    assert 'ensureLabReplayFramesLoaded("prefetch")' in js


def test_lazy_replace_lab_replay_payload_bootstraps_timeline_after_solver_run() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "function bootstrapLabReplayTimeline()" in js
    idx = js.find('lazy.mode === "lazy"')
    chunk = js[idx : idx + 1800]
    assert "bootstrapLabReplayTimeline();" in chunk
    assert "replaySlotForServerInitialFrame();" in chunk
    assert "labReplayLoadState.frameCount > 0 && Boolean(labReplayLoadState.fetchUrl)" in chunk


def test_frame_has_renderable_map_accepts_overlay_and_cell_delta() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    idx = js.find("function frameHasRenderableMap(frame)")
    body = js[idx : idx + 520]
    assert "overlay_cells" in body
    assert "cell_delta" in body


def test_lazy_replay_load_status_retry_click_resets_error() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "function bindLabReplayLoadStatusRetry()" in js
    assert 'ensureLabReplayFramesLoaded("retry")' in js
    assert "[lab-replay] lazy load failed" in js
