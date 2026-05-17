"""A6.1 Lab page context: read-only replay frames for UI (never solver input)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest import mock

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    optimization_replay_frames_to_json_list,
)
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    build_optimization_replay_track_payload,
    empty_optimization_replay_track_payload,
    empty_optimization_replay_track_payload_with_diagnostic,
)
from django_apps.web.services import asteroid_lab_page_context as alc
from django_apps.web.views import public_pages

_OPTIMIZATION_REPLAY_SCRIPT_RE = re.compile(
    r'<script id="optimization-replay-json" type="application/json">(?P<body>.*?)</script>',
    re.DOTALL,
)


def _lab_shell_render_context() -> dict:
    ctx = alc.neutral_lab_context()
    ctx["blueprint_code"] = ""
    ctx["lab_project_slug"] = ""
    return ctx


def _render_lab_shell_html() -> str:
    return render_to_string(
        "web/asteroid_miner_layout_solver.html",
        _lab_shell_render_context(),
        request=RequestFactory().get("/"),
    )


def _parse_optimization_replay_script(html: str) -> dict:
    m = _OPTIMIZATION_REPLAY_SCRIPT_RE.search(html)
    assert m is not None
    return json.loads(m.group("body"))


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
    assert 'optimization_replay|json_script:"optimization-replay-json"' in tpl


def test_lab_template_includes_optimization_replay_json_script() -> None:
    html = _render_lab_shell_html()
    assert 'id="optimization-replay-json"' in html
    assert 'id="optimization-replay-json" type="application/json"' in html.replace("\n", " ")


def test_optimization_replay_json_script_contains_empty_track_by_default() -> None:
    html = _render_lab_shell_html()
    data = _parse_optimization_replay_script(html)
    assert data == empty_optimization_replay_track_payload()


def test_optimization_replay_json_script_is_valid_json() -> None:
    html = _render_lab_shell_html()
    data = _parse_optimization_replay_script(html)
    assert isinstance(data, dict)
    assert "track_id" in data


def test_existing_lab_json_scripts_still_present() -> None:
    html = _render_lab_shell_html()
    for sid in (
        "lab-cell-overlay-matrix-data",
        "lab-runs-data",
        "lab-ui-initial-state",
        "lab-replay-frames-data",
        "lab-initial-replay-frame-data",
    ):
        assert f'id="{sid}"' in html
        assert html.count(f'id="{sid}"') == 1


def test_lab_shell_script_tag_has_js_version_query() -> None:
    html = _render_lab_shell_html().replace("\n", " ")
    assert "asteroid_miner_layout_lab.js?v=" in html


def test_template_renders_when_lab_page_context_omits_optimization_replay() -> None:
    """View helper restores the key so ``json_script`` never sees a missing variable."""

    base = dict(alc.neutral_lab_context())
    del base[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    with mock.patch.object(public_pages, "lab_page_context", return_value=base):
        ctx = public_pages._asteroid_miner_lab_page_context("", project=None)
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == empty_optimization_replay_track_payload()
    html = render_to_string(
        "web/asteroid_miner_layout_solver.html",
        ctx,
        request=RequestFactory().get("/"),
    )
    assert _parse_optimization_replay_script(html) == empty_optimization_replay_track_payload()


def test_template_does_not_include_raw_unescaped_optimization_json() -> None:
    ctx = _lab_shell_render_context()
    malicious = dict(empty_optimization_replay_track_payload())
    malicious["track_label"] = "</script><script>evil()</script>"
    ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] = malicious
    html = render_to_string(
        "web/asteroid_miner_layout_solver.html",
        ctx,
        request=RequestFactory().get("/"),
    )
    m = _OPTIMIZATION_REPLAY_SCRIPT_RE.search(html)
    assert m is not None
    body = m.group("body")
    assert "</script>" not in body
    parsed = json.loads(body)
    assert parsed["track_label"] == malicious["track_label"]


def _read_lab_js() -> str:
    root = Path(__file__).resolve().parents[3]
    js_path = (
        root / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    )
    return js_path.read_text(encoding="utf-8")


def test_lab_js_reads_optimization_replay_json_script_id() -> None:
    js = _read_lab_js()
    assert 'const OPTIMIZATION_REPLAY_SCRIPT_ID = "optimization-replay-json"' in js


def test_lab_js_has_safe_json_script_reader() -> None:
    js = _read_lab_js()
    assert "function readJsonScriptPayload(scriptId, fallback)" in js
    assert "if (!el) return fallback" in js
    assert 'JSON.parse(el.textContent || "null")' in js
    assert "catch (_err)" in js


def test_lab_js_has_optimization_replay_normalizer() -> None:
    js = _read_lab_js()
    assert "function normalizeOptimizationReplayTrack(raw)" in js
    assert "EMPTY_OPTIMIZATION_REPLAY_TRACK" in js
    assert "raw.frames.slice()" in js


def test_lab_js_does_not_reference_optimization_replay_for_rendering() -> None:
    js = _read_lab_js()
    for name in (
        "renderOptimizationReplayFrame(",
        "drawOptimizationOverlay",
        "selectOptimizationTrack",
    ):
        assert name not in js, f"10A must not add {name!r}"
    assert "renderReplayFrame(optimizationReplayTrack" not in js
    assert 'readJsonScript("optimization-replay-json"' not in js


def test_lab_js_does_not_change_existing_replay_script_ids() -> None:
    js = _read_lab_js()
    assert 'readJsonScript("lab-replay-frames-data")' in js


def test_lab_js_no_console_spam_for_optimization_replay() -> None:
    js = _read_lab_js()
    start = js.index("Sequence 10A")
    end = js.index("function getCookie", start)
    chunk = js[start:end]
    assert "console." not in chunk


def _lab_js_sequence_10b_region() -> str:
    js = _read_lab_js()
    start = js.index("Sequence 10B")
    c = js.find("* Sequence 10C", start)
    if c != -1:
        end = c
    else:
        end = js.index("function getCookie", start)
    return js[start:end]


def _lab_js_sequence_10c_region() -> str:
    js = _read_lab_js()
    start = js.index("* Sequence 10C")
    d = js.find("* Sequence 10D", start)
    if d != -1:
        end = d
    else:
        end = js.index("function getCookie", start)
    return js[start:end]


def _lab_js_sequence_10d_region() -> str:
    js = _read_lab_js()
    start = js.index("* Sequence 10D")
    e = js.find("* Sequence 10E", start)
    if e != -1:
        end = e
    else:
        end = js.index("function getCookie", start)
    return js[start:end]


def _lab_js_sequence_10e_region() -> str:
    js = _read_lab_js()
    start = js.index("* Sequence 10E")
    d = js.find("* Sequence 11A", start)
    if d != -1:
        end = d
    else:
        end = js.index("function getCookie", start)
    return js[start:end]


def _lab_js_sequence_11a_region() -> str:
    js = _read_lab_js()
    start = js.index("* Sequence 11A")
    b = js.find("* Sequence 11B", start)
    if b != -1:
        end = b
    else:
        end = js.index("function getCookie", start)
    return js[start:end]


def _lab_js_sequence_11b_region() -> str:
    js = _read_lab_js()
    start = js.index("* Sequence 11B")
    end = js.index("function getCookie", start)
    return js[start:end]


def test_lab_js_registers_optimization_replay_summary() -> None:
    js = _read_lab_js()
    assert js.count("buildOptimizationReplayTrackSummary(optimizationReplayTrack)") == 2


def test_lab_js_has_replace_optimization_replay_payload() -> None:
    js = _read_lab_js()
    assert "function replaceOptimizationReplayPayload(nextPayload)" in js
    i = js.index("function replaceOptimizationReplayPayload")
    j = js.index("* Sequence 11A", i)
    block = js[i:j]
    assert "applyFrame(" not in block


def test_lab_js_has_optimization_replay_frame_count_helper() -> None:
    js = _read_lab_js()
    assert "function optimizationReplayFrameCount(track)" in js


def test_lab_js_has_optimization_replay_event_counts_helper() -> None:
    js = _read_lab_js()
    assert "function optimizationReplayEventTypeCounts(track)" in js


def test_template_includes_optimization_replay_summary_panel() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-replay-summary"' in html


def test_template_includes_optimization_replay_summary_value_target() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-replay-summary-value"' in html


def test_template_includes_optimization_replay_event_counts_target() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-replay-event-counts"' in html


def test_template_includes_optimization_replay_hud_status() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-replay-status"' in html


def test_template_includes_optimization_replay_hud_truncation() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-replay-truncation"' in html


def test_template_includes_optimization_replay_hud_diagnostic() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-replay-diagnostic"' in html


def test_lab_js_has_renderOptimizationReplayHud() -> None:
    js = _read_lab_js()
    assert "function renderOptimizationReplayHud(track)" in js


def test_lab_js_renderOptimizationReplayHud_avoids_currentFrameIndex() -> None:
    js = _read_lab_js()
    start = js.index("* Sequence 12H")
    end = js.index("function formatOptimizationReplayEventCounts", start)
    chunk = js[start:end]
    assert "currentFrameIndex" not in chunk


def test_lab_js_calls_renderOptimizationReplayHud_on_load_and_replace() -> None:
    js = _read_lab_js()
    assert js.count("renderOptimizationReplayHud(optimizationReplayTrack)") == 2


def test_lab_js_formats_optimization_replay_summary() -> None:
    js = _read_lab_js()
    assert "function formatOptimizationReplaySummary(summary)" in js
    assert '(count === 1 ? "" : "s")' in js
    assert "summary.replayTruncated" in js


def test_lab_js_run_solver_fetch_refreshes_optimization_replay_when_present() -> None:
    js = _read_lab_js()
    i = js.index("function runLabBlueprintRebuildViaImportForm")
    j = js.index("const importForm", i)
    block = js[i:j]
    assert "replaceLabReplayPayload(data)" in block
    assert "replaceOptimizationReplayPayload(data.optimization_replay)" in block


def test_lab_js_does_not_read_optimization_frames_by_current_frame_index() -> None:
    js = _read_lab_js()
    assert "optimizationReplayTrack.frames[currentFrameIndex]" not in js


def test_lab_js_does_not_add_track_selector_controls() -> None:
    js = _read_lab_js()
    for needle in (
        "selectOptimizationTrack",
        "lab-optimization-track-select",
        "lab-optimization-replay-timeline",
    ):
        assert needle not in js


def test_existing_lab_replay_controls_still_present() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-timeline-play"' in html
    assert 'id="lab-timeline-scrub"' in html
    assert 'id="lab-timeline-prev"' in html
    assert 'id="lab-timeline-next"' in html


def test_format_optimization_replay_summary_empty() -> None:
    region = _lab_js_sequence_10c_region()
    assert (
        'summary && typeof summary.trackLabel === "string" ? summary.trackLabel : "Optimization"'
        in region
    )
    assert "Number(summary.frameCount)" in region


def test_format_optimization_replay_summary_pluralization() -> None:
    assert '(count === 1 ? "" : "s")' in _lab_js_sequence_10c_region()


def test_format_optimization_replay_summary_truncated() -> None:
    assert '? " · truncated"' in _lab_js_sequence_10c_region()


def test_render_optimization_replay_summary_missing_element_no_throw() -> None:
    region = _lab_js_sequence_10c_region()
    assert "function renderOptimizationReplaySummary(summary)" in region
    assert "if (!el) return" in region
    assert "if (!ev) return" in region


def test_lab_js_sequence_10c_skips_geometry_and_frame_indexing() -> None:
    region = _lab_js_sequence_10c_region()
    assert "visible_cells" not in region
    assert "overlay_cells" not in region
    assert "optimizationReplayTrack.frames[" not in region


def test_selected_optimization_replay_frame_safe_bounds() -> None:
    region = _lab_js_sequence_10d_region()
    assert "function selectedOptimizationReplayFrame(track, frameIndex)" in region
    assert "Number.isInteger(frameIndex)" in region
    assert "frameIndex < 0 || frameIndex >= track.frames.length" in region


def test_selected_optimization_replay_frame_null_when_empty() -> None:
    region = _lab_js_sequence_10d_region()
    assert "return track.frames[frameIndex] || null" in region


def test_format_optimization_replay_frame_metadata_empty() -> None:
    region = _lab_js_sequence_10d_region()
    assert 'title: "No optimization frame selected"' in region
    assert 'metricsSummary: "No metrics"' in region


def test_format_optimization_replay_frame_metadata_event_type() -> None:
    region = _lab_js_sequence_10d_region()
    assert 'typeof frame.event_type === "string"' in region


def test_format_optimization_replay_frame_metadata_metrics_summary() -> None:
    region = _lab_js_sequence_10d_region()
    assert "metricKeys.slice(0, 5).join" in region
    assert "Object.keys(metrics).sort()" in region


def test_lab_js_does_not_render_optimization_geometry() -> None:
    for region in (_lab_js_sequence_10d_region(), _lab_js_sequence_10e_region()):
        for name in (
            "drawOptimizationOverlay",
            "renderOptimizationReplayFrame(",
            "optimizationOverlay",
        ):
            assert name not in region, f"{name!r} must not appear in optimization replay regions"
        assert "visible_cells" not in region
        assert "overlay_cells" not in region


def test_lab_js_does_not_read_visible_cells() -> None:
    assert "visible_cells" not in _lab_js_sequence_10d_region()
    assert "visible_cells" not in _lab_js_sequence_10e_region()


def test_lab_js_does_not_read_overlay_cells() -> None:
    assert "overlay_cells" not in _lab_js_sequence_10d_region()
    assert "overlay_cells" not in _lab_js_sequence_10e_region()


def test_lab_js_does_not_sync_with_current_frame_index() -> None:
    js = _read_lab_js()
    assert "optimizationReplayTrack.frames[currentFrameIndex]" not in js
    assert "selectedOptimizationReplayFrame(optimizationReplayTrack, currentFrameIndex)" not in js


def test_template_contains_optimization_frame_metadata_targets() -> None:
    html = _render_lab_shell_html()
    for sid in (
        "lab-optimization-frame-title",
        "lab-optimization-frame-event",
        "lab-optimization-frame-description",
        "lab-optimization-frame-metrics",
    ):
        assert f'id="{sid}"' in html


def test_template_contains_optimization_frame_navigation_targets() -> None:
    html = _render_lab_shell_html()
    for sid in (
        "lab-optimization-frame-prev",
        "lab-optimization-frame-next",
        "lab-optimization-frame-display",
    ):
        assert f'id="{sid}"' in html


def test_optimization_frame_navigation_buttons_exist() -> None:
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-frame-prev"' in html
    assert 'id="lab-optimization-frame-next"' in html
    assert 'id="lab-optimization-frame-display"' in html


def test_optimization_frame_navigation_uses_independent_index() -> None:
    region = _lab_js_sequence_10e_region()
    assert "let optimizationReplayFrameIndex = 0" in region
    assert "optimizationReplayFrameIndex - 1" in region
    assert "optimizationReplayFrameIndex + 1" in region


def test_optimization_frame_navigation_does_not_modify_lab_frame_index() -> None:
    region = _lab_js_sequence_10e_region()
    assert "currentFrameIndex" not in region
    assert "replayArrayIndex" not in region
    assert "applyFrame(" not in region


def test_optimization_frame_navigation_clamps_bounds() -> None:
    region = _lab_js_sequence_10e_region()
    assert "function clampOptimizationReplayFrameIndex(track, idx)" in region
    assert "Array.isArray(track?.frames)" in region
    assert "Math.min(len - 1, idx)" in region


def test_optimization_frame_navigation_updates_metadata_only() -> None:
    region = _lab_js_sequence_10e_region()
    assert "lab-optimization-frame-display" in region
    assert "formatOptimizationReplayFrameMetadata(frame)" in region
    assert "renderOptimizationReplayFrameMetadata(meta)" in region


def test_lab_js_does_not_sync_optimization_and_lab_timelines() -> None:
    region = _lab_js_sequence_10e_region()
    for needle in (
        "currentFrameIndex",
        "replayArrayIndex",
        "applyFrame(",
        "lab-timeline",
        "scrubEl",
        "setPlaying",
        "setTimelineIndex",
    ):
        assert needle not in region


def test_lab_js_sequence_10e_skips_track_frames_direct_indexing() -> None:
    region = _lab_js_sequence_10e_region()
    assert "optimizationReplayTrack.frames[" not in region


def test_lab_js_sequence_10e_does_not_mutate_optimization_frames() -> None:
    region = _lab_js_sequence_10e_region()
    assert ".frames.push" not in region
    assert ".frames.splice" not in region
    assert "optimizationReplayTrack.frames =" not in region


def test_lab_js_renders_optimization_replay_frame_metadata_via_panel() -> None:
    js = _read_lab_js()
    assert "renderOptimizationReplayFrameMetadata(selectedOptimizationFrameMetadata)" not in js
    region = _lab_js_sequence_10e_region()
    assert "function renderOptimizationReplayFramePanel()" in region
    assert "formatOptimizationReplayFrameMetadata(frame)" in region
    assert "renderOptimizationReplayFrameMetadata(meta)" in region
    assert js.count("renderOptimizationReplayFramePanel();") == 4


def test_render_optimization_replay_frame_metadata_missing_element_no_throw() -> None:
    region = _lab_js_sequence_10d_region()
    assert "function renderOptimizationReplayFrameMetadata(meta)" in region
    assert "if (titleEl) titleEl.textContent" in region


def test_lab_js_sequence_10d_skips_geometry_and_track_frames_indexing() -> None:
    region = _lab_js_sequence_10d_region()
    assert "optimizationReplayTrack.frames[" not in region


def test_lab_js_does_not_render_optimization_overlay() -> None:
    js = _read_lab_js()
    for name in (
        "drawOptimizationOverlay",
        "renderOptimizationReplayFrame(",
        "optimizationOverlay",
    ):
        assert name not in js
    assert "optimizationReplayTrack.frames[" not in js
    assert "visible_cells" not in _lab_js_sequence_10b_region()
    assert "overlay_cells" not in _lab_js_sequence_10b_region()


def test_lab_js_does_not_replace_lab_replay_frames_with_optimization_frames() -> None:
    js = _read_lab_js()
    i = js.index("function replaceLabReplayPayload")
    j = js.index("function syncProjectSlugHiddenFromRedirect", i)
    block = js[i:j]
    assert "optimizationReplayTrack" not in block
    assert "optimizationReplaySummary" not in block
    assert "payload.lab_replay_frames_json" in block


def test_lab_js_does_not_add_backend_calls_for_optimization_replay() -> None:
    js = _read_lab_js()
    gate = js.index("function getCookie")
    tail = js[gate:]
    assert "optimizationReplayTrack" not in tail
    assert "optimizationReplaySummary" not in tail


def test_lab_js_keeps_existing_replay_script_ids() -> None:
    js = _read_lab_js()
    assert js.count('readJsonScript("lab-replay-frames-data")') == 1
    assert js.count('readJsonScript("lab-cell-overlay-matrix-data")') == 1
    assert js.count('readJsonScript("lab-runs-data")') == 1
    assert js.count('readJsonScript("lab-ui-initial-state")') == 1


def test_optimization_replay_track_metadata_uses_track_id_optimization() -> None:
    js = _read_lab_js()
    assert 'trackId: typeof track?.track_id === "string" ? track.track_id : "optimization"' in js


def test_optimization_replay_track_metadata_no_coordinate_interpretation() -> None:
    region = _lab_js_sequence_10b_region()
    assert "visible_cells" not in region
    assert "overlay_cells" not in region
    assert ".frames[" not in region


def test_build_optimization_replay_track_summary_empty() -> None:
    js = _read_lab_js()
    assert "function buildOptimizationReplayTrackSummary(track)" in js
    assert "function optimizationReplayFrameCount(track)" in js
    assert "function hasOptimizationReplayFrames(track)" in js
    assert "track && Array.isArray(track.frames) ? track.frames.length : 0" in js


def test_build_optimization_replay_track_summary_counts() -> None:
    js = _read_lab_js()
    assert "metrics.event_type_counts" in js
    assert "return Object.freeze({ ...counts });" in js


def test_has_optimization_replay_frames_false_for_empty() -> None:
    js = _read_lab_js()
    assert "track.frames.length > 0" in js


def test_has_optimization_replay_frames_true_for_nonempty() -> None:
    js = _read_lab_js()
    assert "Boolean(track && Array.isArray(track.frames) && track.frames.length > 0)" in js


def test_summary_does_not_mutate_frames() -> None:
    region = _lab_js_sequence_10b_region()
    assert ".frames.push" not in region
    assert ".frames.splice" not in region
    assert ".frames =" not in region


def test_template_still_exposes_optimization_replay_json_script() -> None:
    tpl = (
        Path(__file__).resolve().parents[3]
        / "django_apps"
        / "web"
        / "templates"
        / "web"
        / "asteroid_miner_layout_solver.html"
    ).read_text(encoding="utf-8")
    assert 'optimization_replay|json_script:"optimization-replay-json"' in tpl
    assert 'id="optimization-replay-json"' in _render_lab_shell_html()


def test_optimization_replay_missing_payload_fallback_contract_documented() -> None:
    js = _read_lab_js()
    assert "fallback contract" in js
    assert "malformed JSON yields" in js
    assert "EMPTY_OPTIMIZATION_REPLAY_TRACK" in js


def test_read_json_script_payload_missing_returns_fallback() -> None:
    js = _read_lab_js()
    assert "if (!el) return fallback" in js


def test_read_json_script_payload_malformed_returns_fallback() -> None:
    js = _read_lab_js()
    assert "catch (_err)" in js
    assert "return fallback" in js


def test_normalize_optimization_replay_track_accepts_empty_track() -> None:
    js = _read_lab_js()
    assert 'if (!raw || typeof raw !== "object") return EMPTY_OPTIMIZATION_REPLAY_TRACK' in js


def test_normalize_optimization_replay_track_freezes_frames() -> None:
    js = _read_lab_js()
    assert "frames: Object.freeze(frames)" in js


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


@pytest.mark.django_db
def test_optimization_replay_payload_for_project_none_is_empty() -> None:
    assert (
        alc.optimization_replay_payload_for_project(None)
        == empty_optimization_replay_track_payload()
    )


@pytest.mark.django_db
def test_lab_page_context_optimization_replay_from_latest_solver_run() -> None:
    p = m.AsteroidProject.objects.create(name="OptProj", slug="opt-proj-12b")
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
            "t",
            "d",
            (Coord(0, 0),),
            (),
            {},
        ),
    )
    replay_blob = optimization_replay_frames_to_json_list(frames)
    m.SolverRun.objects.create(
        project=p,
        run_key="run-opt-1",
        config_json={SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY: replay_blob},
    )
    ctx = alc.lab_page_context(project_id=p.pk)
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == build_optimization_replay_track_payload(
        frames
    )


@pytest.mark.django_db
def test_lab_page_context_optimization_replay_skips_newer_empty_solver_run() -> None:
    p = m.AsteroidProject.objects.create(name="Skip", slug="skip-empty-run-12b")
    frames = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.GENOME_GENERATED,
            "g",
            "",
            (),
            (),
            {},
        ),
    )
    blob = optimization_replay_frames_to_json_list(frames)
    m.SolverRun.objects.create(project=p, run_key="older", config_json={})
    m.SolverRun.objects.create(
        project=p,
        run_key="old-rich",
        config_json={SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY: blob},
    )
    m.SolverRun.objects.create(project=p, run_key="newer-empty", config_json={})
    ctx = alc.lab_page_context(project_id=p.pk)
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]["frame_count"] == 1
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]["frames"][0]["title"] == "g"


@pytest.mark.django_db
def test_lab_page_context_optimization_replay_project_isolation() -> None:
    pa = m.AsteroidProject.objects.create(name="A", slug="iso-opt-a")
    pb = m.AsteroidProject.objects.create(name="B", slug="iso-opt-b")
    frames_a = (
        OptimizationReplayFrame(
            0,
            OptimizationReplayEventType.VALIDATION_COMPLETED,
            "va",
            "",
            (),
            (),
            {},
        ),
    )
    replay_blob_a = optimization_replay_frames_to_json_list(frames_a)
    m.SolverRun.objects.create(
        project=pa,
        run_key="a1",
        config_json={SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY: replay_blob_a},
    )
    m.SolverRun.objects.create(project=pb, run_key="b1", config_json={})
    ctx_a = alc.lab_page_context(project_id=pa.pk)
    ctx_b = alc.lab_page_context(project_id=pb.pk)
    assert ctx_a[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]["frame_count"] == 1
    assert ctx_b[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == (
        empty_optimization_replay_track_payload_with_diagnostic("missing_optimization_replay")
    )


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


def test_lab_js_sequence_11a_projection_adapter_exists() -> None:
    js = _read_lab_js()
    assert "function projectOptimizationReplayFrameToLabOverlay(frame)" in js


def test_lab_js_sequence_11a_does_not_mutate_lab_frame() -> None:
    region = _lab_js_sequence_11a_region()
    for needle in (
        "getCurrentReplayFrame",
        "replaceLabReplayPayload",
        "applyFrame(",
        "lab_initial_replay_frame",
        "lab-replay-frames-data",
        "cell_overlay_json",
        "frame.visible_cells =",
        "frame.overlay_cells =",
    ):
        assert needle not in region, needle


def test_lab_js_sequence_11a_does_not_sync_frame_indices() -> None:
    region = _lab_js_sequence_11a_region()
    for needle in (
        "currentFrameIndex",
        "optimizationReplayFrameIndex",
        "replayArrayIndex",
    ):
        assert needle not in region, needle


def test_lab_js_sequence_11a_records_projection_diagnostics() -> None:
    region = _lab_js_sequence_11a_region()
    for key in (
        "inputVisibleCellCount",
        "inputOverlayCellCount",
        "projectedCellCount",
        "droppedCellCount",
        "dropReasons",
    ):
        assert key in region, key
    assert "missing_lab_projection_bbox" in region


def test_lab_js_sequence_11b_overlay_feature_flag_exists() -> None:
    js = _read_lab_js()
    assert "const ENABLE_LAB_OPTIMIZATION_OVERLAY = false" in js


def test_lab_js_sequence_11b_overlay_layer_id_exists() -> None:
    js = _read_lab_js()
    assert 'getElementById("lab-optimization-overlay-layer")' in js
    html = _render_lab_shell_html()
    assert 'id="lab-optimization-overlay-layer"' in html
    assert 'id="lab-optimization-overlay-diagnostics"' in html


def test_lab_js_sequence_11b_render_consumes_projection_adapter() -> None:
    region = _lab_js_sequence_11b_region()
    assert "function renderOptimizationReplayOverlay()" in region
    assert "projectOptimizationReplayFrameToLabOverlay(frame)" in region
    assert "function renderLabOptimizationOverlayCells(projectionCells)" in region


def test_lab_js_sequence_11b_render_does_not_mutate_lab_frame() -> None:
    region = _lab_js_sequence_11b_region()
    for needle in (
        "replaceLabReplayPayload",
        "getCurrentReplayFrame",
        "applyFrame(",
        "cell_overlay_json",
        "lab-replay-frames-data",
    ):
        assert needle not in region, needle


def test_lab_js_sequence_11b_render_does_not_sync_indices() -> None:
    region = _lab_js_sequence_11b_region()
    for needle in (
        "currentFrameIndex",
        "optimizationReplayFrameIndex",
        "replayArrayIndex",
    ):
        assert needle not in region, needle


def test_lab_js_sequence_11b_clear_overlay_exists() -> None:
    js = _read_lab_js()
    assert "function clearOptimizationReplayOverlay()" in js
    assert "lab-optimization-overlay-layer" in _lab_js_sequence_11b_region()


def test_lab_js_sequence_11b_does_not_mutate_optimization_cells() -> None:
    region = _lab_js_sequence_11b_region()
    assert "visible_cells =" not in region
    assert "overlay_cells =" not in region


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
