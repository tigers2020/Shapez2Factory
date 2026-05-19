"""A6.1 Lab page context: read-only replay frames for UI (never solver input)."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    persist_optimization_replay_frames_to_solver_run,
)
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY,
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_pipeline import run_solver_runtime_pipeline
from django_apps.web.services import asteroid_lab_page_context as alc

_GENE_TEMPLATES = (
    Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"
)


@pytest.mark.django_db
def test_lab_page_context_neutral_when_no_replay_frames() -> None:
    m.AsteroidProject.objects.create(name="Empty", slug="empty-lab-ctx")
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is False
    assert ctx["total_frames"] == 0
    assert ctx["lab_replay_frames_json"] == []
    assert ctx["lab_initial_replay_frame_json"] == {}


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


@pytest.mark.django_db
def test_lab_page_context_includes_empty_optimization_replay_when_no_solver_run() -> None:
    p = m.AsteroidProject.objects.create(name="OptEmpty", slug="opt-empty-lab-ctx")
    ctx = alc.lab_page_context(project_id=p.pk)
    opt = ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    assert opt["frames"] == []
    assert (
        opt["metrics"][OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY]
        == "missing_optimization_replay"
    )


@pytest.mark.django_db
def test_lab_page_context_reads_persisted_optimization_replay() -> None:
    import base64
    import gzip
    import json
    import random

    from django.test import Client
    from django.urls import reverse

    from django_apps.asteroid_lab.optimization.loaded_snapshot import (
        loaded_reconstruction_snapshot_from_result,
    )
    from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
        run_reconstruction_for_map_input,
    )

    def _copy() -> str:
        root = {
            "V": random.randint(1, 10_000_000),
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                    {"X": 3, "Y": 1, "T": "Layout_ShapeMinerExtension"},
                ],
            },
        }
        text = json.dumps(root, separators=(",", ":")).encode("utf-8")
        return "SHAPEZ2-4-" + base64.b64encode(gzip.compress(text)).decode("ascii")

    client = Client()
    client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": _copy()},
        follow=True,
    )
    proj = m.AsteroidProject.objects.get()
    inp = m.AsteroidMapInput.objects.filter(project=proj).order_by("-id").first()
    assert inp is not None
    _cleanup, recon = run_reconstruction_for_map_input(int(inp.pk))
    loaded = loaded_reconstruction_snapshot_from_result(recon)
    run_dto = create_solver_run(
        int(proj.pk),
        run_key="ctx-opt-read",
        algorithm_label="runtime_v0",
        config={},
    )
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_template_path=_GENE_TEMPLATES / "minimal_extractor_e.json",
    )
    persist_optimization_replay_frames_to_solver_run(
        run_dto.id,
        result.replay_frames,
        solver_summary=result.solver_summary,
    )

    ctx = alc.lab_page_context(project_id=proj.pk)
    opt = ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    assert len(opt["frames"]) >= 1
    assert opt["metrics"]["frame_count"] == len(opt["frames"])
    assert OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY not in opt["metrics"]
    event_types = {f["event_type"] for f in opt["frames"]}
    assert OptimizationReplayEventType.VALIDATION_COMPLETED.value in event_types


@pytest.mark.django_db
def test_lab_page_context_malformed_optimization_replay_does_not_crash() -> None:
    p = m.AsteroidProject.objects.create(name="OptBad", slug="opt-bad-lab-ctx")
    m.SolverRun.objects.create(
        project=p,
        run_key="bad-opt",
        algorithm_label="runtime_v0",
        config_json={SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY: [{"frame_index": 99}]},
    )
    ctx = alc.lab_page_context(project_id=p.pk)
    opt = ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    assert opt["frames"] == []
    assert (
        opt["metrics"][OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY]
        == "invalid_optimization_replay_payload"
    )


@pytest.mark.django_db
def test_lab_page_context_optimization_replay_does_not_touch_lab_replay_orm() -> None:
    p = m.AsteroidProject.objects.create(name="OptOrm", slug="opt-orm-lab-ctx")
    t = m.ReplayTrack.objects.create(project=p, track_key="opt-tr")
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
    alc.lab_page_context(project_id=p.pk)
    assert m.ReplayFrame.objects.count() == before


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
        "django_apps.shapez_asteroid",
        "django_apps.shapez_core",
        "django_apps.shapez_solver",
        "asteroid_mining_layout_v1",
        "asteroid_mining_layout_v2",
    )
    for bad in forbidden:
        assert bad not in text, f"asteroid_lab_page_context must not mention {bad!r}"


def test_lab_js_replay_wiring_smoke() -> None:
    root = Path(__file__).resolve().parents[3]
    js_path = (
        root / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    )
    js = js_path.read_text(encoding="utf-8")
    assert "lab-identifier-sprite-paths-data" in js
    assert "labIdentifierSpriteRelpaths" in js
    assert "combineSpriteRotation" not in js
    assert "normalizeQuarterTurns(cell.rotation)" in js
    assert "normalizeQuarterTurns" in js
    assert "rotationToDeg" in js
    assert "quarter 0 = E = 0deg" in js
    assert "1 = S = 90deg clockwise on screen" in js
    assert "scaleX(-1)" not in js
    assert "rotateY(180deg)" not in js
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
    assert "lab-timeline-controls" in js
    assert "labPointerShouldStartViewportPan" in js
    assert "endLabViewportPan" in js
    assert 'closest("#lab-timeline-controls, #lab-timeline-scrub")' in js
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
    assert 'translate(" + tx + "px, " + ty + "px) scale(" + zoom + ")"' in js
    assert "gridViewport.style.transform" not in js
    assert "gridViewport.style.width" not in js
    assert "gridViewport.style.height" not in js

    tpl_path = (
        root / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
    )
    tpl = tpl_path.read_text(encoding="utf-8")
    assert 'id="lab-timeline-controls"' in tpl
    assert "data-lab-timeline-controls" in tpl
    controls_idx = tpl.index('id="lab-timeline-controls"')
    scrub_idx = tpl.index('id="lab-timeline-scrub"', controls_idx)
    assert scrub_idx > controls_idx
    assert "lab_identifier_sprite_paths" in tpl
    assert "lab-identifier-sprite-paths-data" in tpl
