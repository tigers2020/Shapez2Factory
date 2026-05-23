"""A6.1 Lab page context: read-only replay frames for UI (never solver input)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from django.template import Context, Template

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.web.services import asteroid_lab_page_context as alc


@pytest.mark.django_db
def test_lab_page_context_includes_solver_runs_for_project() -> None:
    proj = m.AsteroidProject.objects.create(name="RunsCtx", slug="runs-ctx-lab")
    m.SolverRun.objects.create(
        project=proj,
        run_key="r1",
        algorithm_label="runtime_v0",
        status=m.SolverRun.RunStatus.FAILED,
        config_json={
            SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {
                "validation_passed": False,
                "confirmed_count": 0,
                "issue_codes": ["orphan_transport"],
            }
        },
    )
    ctx = alc.lab_page_context(project_id=proj.pk)
    assert len(ctx["runs"]) == 1
    assert ctx["runs"][0]["id"] is not None
    assert ctx["runs"][0]["status"] == "failed"
    assert ctx["runs"][0]["first_issue_code"] == "orphan_transport"


def test_lab_cell_neutral_rounded_rect_not_circle() -> None:
    """Lab SSR cells use h-7 w-7; radius comes from CSS --lab-cell-radius, not rounded-[5px]."""

    assert "h-7 w-7" in alc.LAB_CELL_NEUTRAL
    assert "rounded-[5px]" not in alc.LAB_CELL_NEUTRAL


@pytest.mark.django_db
def test_lab_page_context_neutral_when_no_replay_frames() -> None:
    m.AsteroidProject.objects.create(name="Empty", slug="empty-lab-ctx")
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is False
    assert ctx["total_frames"] == 0
    assert ctx["lab_replay_frames_json"] == []
    assert ctx["lab_initial_replay_frame_json"] == {}


@pytest.mark.django_db
def test_unified_payload_authoritative_no_optimization_replay_track() -> None:
    """Page context must expose lab_replay_frames_json (single replay timeline)
    and must NOT contain the legacy optimization_replay top-level key."""
    ctx = alc.neutral_lab_context()
    assert "lab_replay_frames_json" in ctx
    assert "replay_track_metrics" in ctx
    # 9E contract: dual-track key must not appear in page context
    assert "optimization_replay" not in ctx


@pytest.mark.django_db
def test_lab_page_context_neutral_when_latest_track_has_zero_frames() -> None:
    p = m.AsteroidProject.objects.create(name="NoFrames", slug="no-frames-lab")
    m.ReplayTrack.objects.create(project=p, track_key="empty-track")
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is False
    assert ctx["total_frames"] == 0


@pytest.mark.django_db
def test_lab_page_context_without_project_id_is_neutral() -> None:
    p = m.AsteroidProject.objects.create(name="Scoped", slug="scoped-lab-ctx")
    t = m.ReplayTrack.objects.create(project=p, track_key="scoped-tr")
    m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="x",
        phase="decode",
        title="T",
        description="",
        frame_payload={
            "event_type": "decode.raw_loaded",
            "full_map": [{"x": 1, "y": 0, "cell_kind": "asteroid", "transport_kind": "none"}],
        },
        cell_overlay_json={},
    )
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is False
    assert ctx["lab_replay_frames_json"] == []


@pytest.mark.django_db
def test_lab_page_context_orders_frames_by_frame_index_then_id() -> None:
    p = m.AsteroidProject.objects.create(name="Ord", slug="ord-lab-ctx")
    t = m.ReplayTrack.objects.create(project=p, track_key="ord-tr")
    for fi, fk, ev, x in (
        (0, "a", "decode.raw_loaded", 1),
        (1, "b", "decode.normalized", 2),
    ):
        m.ReplayFrame.objects.create(
            replay_track=t,
            frame_index=fi,
            frame_key=fk,
            phase="decode",
            title=fk.upper(),
            description="",
            frame_payload={
                "event_type": ev,
                "phase": "decode",
                "phase_step": "raw" if fi == 0 else "normalized",
                "event_key": f"step{fi}",
                "full_map": [{"x": x, "y": 0, "cell_kind": "asteroid", "transport_kind": "none"}],
            },
            cell_overlay_json={},
        )
    ctx = alc.lab_page_context(project_id=p.pk)
    indices = [f["frame_index"] for f in ctx["lab_replay_frames_json"]]
    assert indices == [0, 1]
    assert ctx["lab_replay_frames_json"][0]["event_type"] == ReplayEventType.DECODE_STARTED.value
    assert ctx["initial_frame"] == 0
    assert ctx["total_frames"] == 2
    assert _LAB_FRAME_DISPLAY_SNIPPET.render(
        Context({"initial_frame": ctx["initial_frame"], "total_frames": ctx["total_frames"]}),
    ) == "1 / 2"


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
    assert len(frames) >= 6
    assert ctx["total_frames"] == len(frames)
    event_types = {f["event_type"] for f in frames}
    assert ReplayEventType.DECODE_STARTED.value in event_types
    assert ReplayEventType.RECONSTRUCTION_COMPLETED.value in event_types
    assert isinstance(frames[0]["map_view"], dict)
    with_bundles = [
        f
        for f in frames
        if isinstance(f.get("cell_overlay_json"), dict)
        and f["cell_overlay_json"].get("equipment_bundles")
    ]
    assert (
        with_bundles
    ), "decode/replay frames must expose cell_overlay_json.equipment_bundles for Lab highlight"
    with_replay_frame_id = [
        f
        for f in frames
        if isinstance(f.get("inspector"), dict)
        and f["inspector"].get("replay_frame_id") is not None
    ]
    assert (
        with_replay_frame_id
    ), "Lab ORM frames must expose inspector.replay_frame_id for cell detail POST"
    first_rid = int(with_replay_frame_id[0]["inspector"]["replay_frame_id"])
    row = m.ReplayFrame.objects.get(pk=first_rid)
    assert int(row.replay_track_id) == int(tid)


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
def test_lab_page_context_read_does_not_touch_lab_replay_orm() -> None:
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


@pytest.mark.django_db
def test_lab_page_context_exposes_replay_track_metrics() -> None:
    p = m.AsteroidProject.objects.create(name="Metrics", slug="metrics-ctx")
    t = m.ReplayTrack.objects.create(project=p, track_key="metrics-tr")
    m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="a",
        phase="decode",
        title="A",
        description="",
        frame_payload={
            "event_type": "decode.raw_loaded",
            "phase": "decode",
            "phase_step": "raw",
            "event_key": "step0",
            "full_map": [{"x": 1, "y": 0, "cell_kind": "asteroid", "transport_kind": "none"}],
        },
        cell_overlay_json={},
    )
    ctx = alc.lab_page_context(project_id=p.pk)
    metrics = ctx["replay_track_metrics"]
    assert metrics["frame_count"] == len(ctx["lab_replay_frames_json"])
    assert metrics["replay_truncated"] is False


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
    assert "LAB_SPRITE_CELL_KIND_STATIC_RELPATH" in js
    assert "AsteroidField_Fluid.svg" in js
    assert "AsteroidField_Shape.svg" in js
    assert "LAB_SPRITE_TILE_TYPE_ALIASES" in js
    assert "Layout_ProMiner" in js
    assert 'startsWith("Layout_")' in js
    assert 'return "Miner/" + t + ".svg"' in js
    assert "asteroid_fluid_field" in js
    assert "asteroid_shape_field" in js
    assert "snapToDevicePixel" in js
    assert "data-lab-sprite-base" in js
    assert "function renderReplayFrame" in js
    assert "overlayCellsFromMapView(mapView)" in js
    assert "cellDeltaCellsFromMapView(mapView)" in js
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
    assert "lab-replay-track-metrics-data" in tpl
    assert 'id="lab-replay-run-status"' in tpl
    assert 'id="lab-evolution-runs-list"' in tpl
    assert "lab-detail-first-issue" in tpl
    assert "lab-detail-placed" in tpl
    assert "lab-detail-issue-coord" in tpl
    assert "lab-detail-status" in tpl
    assert "lab-optimization-replay-data" not in tpl
    assert 'id="lab-optimization-replay-attach"' not in tpl
    assert "Optimization Replay" not in tpl
    assert "data-lab-run-solver-url" in tpl
    assert "function renderReplayRunStatus" in js
    assert "lab-replay-track-metrics-data" in js
    assert "function replaceOptimizationReplayPayload" not in js
    assert "renderOptimizationReplayAttachHud" not in js
    assert "function renderEvolutionRunsList" in js
    assert "function upsertRunSummary" in js
    assert "lab-evolution-runs-list" in js
    assert "lab-detail-first-issue" in js
    assert "lab-detail-placed" in js
    assert "lab-detail-issue-coord" in js
    assert "lab-detail-status" in js
    assert "labRunSolverUrl" in js
    assert "function syncLabProjectEndpoints" in js
    assert "run_solver_url" in js
    assert 'method: "POST"' in js
    assert "dataset.labRunSolverUrl" in js
    run_btn_idx = js.index("runSolverBtn")
    run_handler = js[run_btn_idx : run_btn_idx + 2500]
    assert "setPlaying(true)" not in run_handler
    assert "replaceLabReplayPayload" in run_handler
    assert "seekLastFrame: true" in js
    assert "currentUnifiedFrameIndex" not in js
    assert "lab-unified-replay-data" not in js
    assert "updateReplayTruncationHud" in js
    assert 'id="lab-replay-truncation-hud"' in tpl
    assert "function formatLabFrameCounter(zeroBasedSlot, totalCount)" in js
    assert "formatLabFrameCounter(replayArrayIndex, replayFrames.length)" in js
    assert '{{ initial_frame|add:1 }} / {{ total_frames }}' in tpl


_LAB_FRAME_DISPLAY_SNIPPET = Template(
    "{% if total_frames %}{{ initial_frame|add:1 }} / {{ total_frames }}"
    "{% else %}0 / 0{% endif %}"
)

_FORMAT_LAB_FRAME_COUNTER_JS = """
function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
function formatLabFrameCounter(zeroBasedSlot, totalCount) {
  const total = Number.isFinite(totalCount) && totalCount > 0 ? Math.floor(totalCount) : 0;
  if (total <= 0) {
    return "0 / 0";
  }
  const slot = Number.isFinite(zeroBasedSlot) ? Math.floor(zeroBasedSlot) : 0;
  const clamped = clampNumber(slot, 0, total - 1);
  return String(clamped + 1) + " / " + String(total);
}
const payload = JSON.parse(process.argv[1]);
console.log(formatLabFrameCounter(payload.slot, payload.total));
"""


def _eval_format_lab_frame_counter_js(*, slot: object, total: int) -> str:
    if shutil.which("node") is None:
        pytest.skip("node not on PATH")
    proc = subprocess.run(
        ["node", "-e", _FORMAT_LAB_FRAME_COUNTER_JS, json.dumps({"slot": slot, "total": total})],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def test_lab_frame_display_ssr_renders_one_based_counter() -> None:
    assert _LAB_FRAME_DISPLAY_SNIPPET.render(
        Context({"initial_frame": 0, "total_frames": 22}),
    ) == "1 / 22"
    assert _LAB_FRAME_DISPLAY_SNIPPET.render(
        Context({"initial_frame": 21, "total_frames": 22}),
    ) == "22 / 22"
    assert _LAB_FRAME_DISPLAY_SNIPPET.render(
        Context({"initial_frame": 0, "total_frames": 0}),
    ) == "0 / 0"


@pytest.mark.parametrize(
    ("slot", "total", "expected"),
    [
        (0, 22, "1 / 22"),
        (21, 22, "22 / 22"),
        (None, 22, "1 / 22"),
    ],
)
def test_format_lab_frame_counter_js(slot: object, total: int, expected: str) -> None:
    assert _eval_format_lab_frame_counter_js(slot=slot, total=total) == expected
