"""A6.1 Lab page context: read-only replay frames for UI (never solver input)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    empty_optimization_replay_track_payload,
)
from django_apps.web.services import asteroid_lab_page_context as alc


def test_neutral_lab_context_includes_empty_optimization_replay() -> None:
    ctx = alc.neutral_lab_context()
    assert OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY in ctx
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == empty_optimization_replay_track_payload()


@pytest.mark.django_db
def test_lab_page_context_includes_optimization_replay_key() -> None:
    m.AsteroidProject.objects.create(name="Empty", slug="empty-opt-replay-key")
    ctx = alc.lab_page_context()
    assert OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY in ctx


@pytest.mark.django_db
def test_optimization_replay_context_payload_is_empty_track_by_default() -> None:
    p = m.AsteroidProject.objects.create(name="WithLabReplay", slug="with-lab-replay-opt")
    t = m.ReplayTrack.objects.create(project=p, track_key="tr-opt")
    m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="f0",
        phase="decode",
        title="T",
        description="",
        frame_payload={"event_type": "decode.raw_loaded"},
        cell_overlay_json={},
    )
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is True
    opt = ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    assert opt == empty_optimization_replay_track_payload()
    assert opt["frame_count"] == 0
    assert opt["frames"] == []


@pytest.mark.django_db
def test_existing_lab_context_fields_preserved() -> None:
    m.AsteroidProject.objects.create(name="Preserve", slug="preserve-lab-fields")
    neutral = alc.neutral_lab_context()
    ctx = alc.lab_page_context()
    for key in neutral:
        if key == OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY:
            continue
        assert key in ctx
        assert ctx[key] == neutral[key]


@pytest.mark.django_db
def test_context_optimization_replay_json_safe() -> None:
    m.AsteroidProject.objects.create(name="JsonSafe", slug="json-safe-opt")
    ctx = alc.lab_page_context()
    json.dumps(ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY])


@pytest.mark.django_db
def test_context_does_not_invoke_optimizer_runner() -> None:
    m.AsteroidProject.objects.create(name="NoRunner", slug="no-runner-opt")
    p = "django_apps.shapez_asteroid.optimization.optimization_ui_payload"
    with (
        mock.patch(f"{p}.build_optimization_replay_track_payload") as build_track,
        mock.patch(f"{p}.optimization_replay_frame_to_json_dict") as frame_to_json,
    ):
        alc.neutral_lab_context()
        alc.lab_page_context()
    build_track.assert_not_called()
    frame_to_json.assert_not_called()


def test_context_template_payload_backward_compatible_if_template_touched() -> None:
    root = Path(__file__).resolve().parents[3]
    tpl = (
        root / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
    ).read_text(encoding="utf-8")
    assert 'lab_replay_frames_json|json_script:"lab-replay-frames-data"' in tpl
    assert "optimization_replay" not in tpl


@pytest.mark.django_db
def test_lab_page_context_neutral_when_no_replay_frames() -> None:
    m.AsteroidProject.objects.create(name="Empty", slug="empty-lab-ctx")
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is False
    assert ctx["total_frames"] == 0
    assert ctx["lab_replay_frames_json"] == []
    assert ctx["lab_initial_replay_frame_json"] == {}
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == empty_optimization_replay_track_payload()


@pytest.mark.django_db
def test_lab_page_context_neutral_when_latest_track_has_zero_frames() -> None:
    p = m.AsteroidProject.objects.create(name="NoFrames", slug="no-frames-lab")
    m.ReplayTrack.objects.create(project=p, track_key="empty-track")
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is False
    assert ctx["total_frames"] == 0


@pytest.mark.django_db
def test_lab_page_context_picks_latest_track_with_frames() -> None:
    p1 = m.AsteroidProject.objects.create(name="Old", slug="old-lab-ctx")
    t1 = m.ReplayTrack.objects.create(project=p1, track_key="old-tr")
    m.ReplayFrame.objects.create(
        replay_track=t1,
        frame_index=0,
        frame_key="old",
        phase="decode",
        title="Old",
        description="",
        frame_payload={"event_type": "decode.raw_loaded"},
        cell_overlay_json={},
    )
    p2 = m.AsteroidProject.objects.create(name="New", slug="new-lab-ctx")
    t2 = m.ReplayTrack.objects.create(project=p2, track_key="new-tr")
    m.ReplayFrame.objects.create(
        replay_track=t2,
        frame_index=0,
        frame_key="new",
        phase="existing_layout",
        title="Newer",
        description="d",
        frame_payload={"event_type": "existing_layout.begin"},
        cell_overlay_json={"cells": [{"x": 1, "y": 2, "cell_kind": "miner"}]},
    )
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is True
    assert ctx["lab_replay_track_id"] == t2.id
    assert ctx["lab_replay_track_key"] == "new-tr"
    assert ctx["total_frames"] == 1
    assert ctx["initial_frame"] == 0
    frames = ctx["lab_replay_frames_json"]
    assert len(frames) == 1
    assert frames[0]["frame_key"] == "new"
    assert frames[0]["event_type"] == "existing_layout.begin"
    assert frames[0]["cell_overlay_json"]["cells"][0]["x"] == 1


@pytest.mark.django_db
def test_lab_page_context_orders_frames_by_frame_index_then_id() -> None:
    p = m.AsteroidProject.objects.create(name="Ord", slug="ord-lab-ctx")
    t = m.ReplayTrack.objects.create(project=p, track_key="ord-tr")
    m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=1,
        frame_key="b",
        phase="p",
        title="B",
        description="",
        frame_payload={"event_type": "decode.normalized"},
        cell_overlay_json={},
    )
    a = m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="a",
        phase="p",
        title="A",
        description="",
        frame_payload={"event_type": "decode.raw_loaded"},
        cell_overlay_json={},
    )
    ctx = alc.lab_page_context()
    keys = [f["frame_key"] for f in ctx["lab_replay_frames_json"]]
    assert keys == ["a", "b"]
    assert ctx["lab_initial_replay_frame_json"]["id"] == a.id


@pytest.mark.django_db
def test_lab_page_context_after_pipeline_selects_non_empty_track() -> None:
    import base64
    import gzip
    import json

    from django_apps.asteroid_lab.services import project_service
    from django_apps.asteroid_lab.services.replay_pipeline_service import (
        build_initial_replay_for_map_input,
    )

    root = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    code = "SHAPEZ2-4-" + base64.b64encode(gzip.compress(text)).decode("ascii")
    dto = project_service.create_project_from_copy_code(code, source_label="ctx-pipe")
    build_initial_replay_for_map_input(dto.map_input_id)

    ctx = alc.lab_page_context(project_id=dto.project_id)
    assert ctx["has_replay_frames"] is True
    frames = ctx["lab_replay_frames_json"]
    tid = ctx["lab_replay_track_id"]
    assert tid is not None
    assert len(frames) == m.ReplayFrame.objects.filter(replay_track_id=tid).count()
    assert len(frames) >= 6
    assert ctx["total_frames"] == len(frames)
    assert frames[0]["event_type"] == et.EVENT_TYPE_DECODE_RAW_LOADED
    assert frames[0]["frame_key"] == "step0_decode_raw"
    assert frames[1]["event_type"] == et.EVENT_TYPE_DECODE_NORMALIZED
    assert frames[1]["frame_key"] == "step0_decode"


@pytest.mark.django_db
def test_lab_page_context_does_not_create_replay_rows() -> None:
    p = m.AsteroidProject.objects.create(name="Cnt", slug="cnt-lab-ctx")
    t = m.ReplayTrack.objects.create(project=p, track_key="cnt-tr")
    m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="x",
        phase="decode",
        title="T",
        description="",
        frame_payload={"event_type": "decode.raw_loaded"},
        cell_overlay_json={},
    )
    before = m.ReplayFrame.objects.count()
    alc.lab_page_context()
    assert m.ReplayFrame.objects.count() == before


@pytest.mark.django_db
def test_lab_page_context_restricted_to_project_id() -> None:
    p1 = m.AsteroidProject.objects.create(name="A", slug="ctx-scoped-a")
    t1 = m.ReplayTrack.objects.create(project=p1, track_key="a-tr")
    m.ReplayFrame.objects.create(
        replay_track=t1,
        frame_index=0,
        frame_key="a",
        phase="p",
        title="A",
        description="",
        frame_payload={"event_type": "decode.raw_loaded"},
        cell_overlay_json={},
    )
    p2 = m.AsteroidProject.objects.create(name="B", slug="ctx-scoped-b")
    t2 = m.ReplayTrack.objects.create(project=p2, track_key="b-tr")
    m.ReplayFrame.objects.create(
        replay_track=t2,
        frame_index=0,
        frame_key="b",
        phase="p",
        title="B",
        description="",
        frame_payload={"event_type": "decode.normalized"},
        cell_overlay_json={},
    )
    ctx_a = alc.lab_page_context(project_id=p1.pk)
    assert ctx_a["lab_replay_track_id"] == t1.id
    ctx_b = alc.lab_page_context(project_id=p2.pk)
    assert ctx_b["lab_replay_track_id"] == t2.id


def test_lab_page_context_module_import_boundary() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "django_apps"
        / "web"
        / "services"
        / "asteroid_lab_page_context.py"
    )
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "django_apps.shapez_core",
        "django_apps.shapez_solver",
        "asteroid_mining_layout_v1",
        "asteroid_mining_layout_v2",
    )
    for bad in forbidden:
        assert bad not in text, f"asteroid_lab_page_context must not mention {bad!r}"
    if "django_apps.shapez_asteroid" in text:
        allowed = "from django_apps.shapez_asteroid.optimization.optimization_ui_payload import"
        assert allowed in text, (
            "shapez_asteroid imports are limited to optimization_ui_payload "
            "(Sequence 9B lab optimization replay payload seam)"
        )
        assert text.count("django_apps.shapez_asteroid") == 1


def test_lab_js_replay_wiring_smoke() -> None:
    root = Path(__file__).resolve().parents[3]
    js_path = (
        root / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    )
    js = js_path.read_text(encoding="utf-8")
    assert "LAB_SPRITE_KNOWN" in js
    assert "LAB_SPRITE_REGISTRY" in js
    assert "labPascalSegmentToSnakeLower" in js
    assert '.startsWith("SpacePipe_")' in js
    assert "combineSpriteRotation" in js
    assert "normalizeQuarterTurns" in js
    assert "LINK_KEY_TO_DIR" in js
    assert "DIR_TO_BRIDGE_SUFFIX" in js
    assert "lab-cell-sprite" in js
    assert "snapToDevicePixel" in js
    assert "data-lab-sprite-base" in js
    assert "function renderReplayFrame" in js
    assert "getCurrentReplayFrame" in js
    assert "lab-replay-frames-data" in js
    assert "lab-timeline-play" in js
    assert "lab-timeline-scrub" in js
    assert "setTimelineIndex" in js
    assert "hasServerReplay" in js
    assert "replayPhaseForFrame" in js
    assert "updateFrameInfo" in js
    assert "replaceLabReplayPayload" in js
    assert "bootStartedWithServerReplay" not in js
    assert "syncProjectSlugHiddenFromRedirect" in js
    assert "lab-replay-grid-stage" in js
    assert "bindLabViewportInteractions" in js
    assert "LAB_VIEWPORT_MIN_SCALE" in js
    assert "__shapezLabReplaySelfTestViewportZoomStability" in js


def test_lab_replay_stage_absolute_inset_template_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    tpl = (
        root / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
    ).read_text(encoding="utf-8")
    assert 'id="lab-replay-grid-stage"' in tpl
    assert "absolute inset-4" in tpl


def test_lab_replay_viewport_css_layout_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    css = (root / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert "contain: layout paint" in css
    assert "transform: none" in css
    assert "#lab-replay-grid-stage" in css
    marker = "#lab-replay-grid-stage {"
    assert marker in css
    start = css.index(marker)
    stage_block = css[start : start + 520]
    assert "position: absolute" in stage_block
