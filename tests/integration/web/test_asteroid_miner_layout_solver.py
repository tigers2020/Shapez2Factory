import base64
import gzip
import json
import random
import unittest.mock as mock
from pathlib import Path

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    OptimizationReplayAttachResult,
    build_optimization_replay_attach_diagnostic,
)
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    build_optimization_replay_track_payload,
    deserialize_optimization_replay_frames_from_json,
    empty_optimization_replay_track_payload,
    empty_optimization_replay_track_payload_with_diagnostic,
)
from django_apps.web.services import asteroid_lab_page_context as alc
from tests.support.measure_json_sections import (
    assert_lab_replay_not_capped_by_optimization_constants,
    assert_optimization_replay_hard_caps,
    measure_json_sections,
)

pytestmark = [pytest.mark.django_db, pytest.mark.slow]


def _read_asteroid_lab_js_text() -> str:
    root = Path(__file__).resolve().parents[3]
    return (
        root / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")


def _lab_html_with_optimization_replay(client: Client, opt_payload: dict) -> str:
    ctx = {**alc.neutral_lab_context(), OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY: opt_payload}
    with mock.patch("django_apps.web.views.public_pages.lab_page_context", return_value=ctx):
        response = client.get(reverse("web:asteroid-miner-layout"))
    assert response.status_code == 200
    return response.content.decode()


def _valid_truncated_optimization_track() -> dict:
    raw = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {"replay_truncated": True, "truncation_reason": "cells_reason_xyz"},
        }
    ]
    frames = deserialize_optimization_replay_frames_from_json(raw)
    assert frames is not None
    return build_optimization_replay_track_payload(frames)


def _valid_normal_optimization_track() -> dict:
    raw = [
        {
            "frame_index": 0,
            "event_type": OptimizationReplayEventType.CANDIDATE_GENERATED.value,
            "title": "t",
            "description": "",
            "visible_cells": [],
            "overlay_cells": [],
            "metrics": {},
        }
    ]
    frames = deserialize_optimization_replay_frames_from_json(raw)
    assert frames is not None
    return build_optimization_replay_track_payload(frames)


def _assert_optimization_replay_lab_payload(data: dict) -> None:
    """12E: lab JSON must carry real optimization replay frames (event_type contract)."""

    opt = data.get(OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY)
    assert isinstance(opt, dict)
    assert opt.get("track_id") == "optimization"
    assert int(opt.get("frame_count") or 0) >= 1
    frames = opt.get("frames") or []
    assert isinstance(frames, list) and len(frames) >= 1
    assert isinstance(frames[0], dict)
    assert "event_type" in frames[0] and isinstance(frames[0]["event_type"], str)
    event_types = [
        f["event_type"]
        for f in frames
        if isinstance(f, dict) and isinstance(f.get("event_type"), str)
    ]
    assert any(
        et.startswith("candidate.")
        or et.startswith("route_probe.")
        or et.startswith("generation.")
        or et.startswith("genome.")
        or et.startswith("optimization.")
        or et.startswith("pattern.")
        or et.startswith("best_genome.")
        for et in event_types
    )


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _unique_valid_copy() -> str:
    return _encode_v4_copy(
        {
            "V": random.randint(1, 10_000_000),
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        }
    )


def test_asteroid_miner_layout_page_renders_lab_shell() -> None:
    response = Client().get(reverse("web:asteroid-miner-layout"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Asteroid Mining Lab" in content
    assert "Greenfield Solver Workspace" in content
    assert "Replay Timeline" in content
    assert "lab-cell-overlay-matrix-data" in content
    assert 'id="lab-ui-initial-state"' in content
    assert "G-042" not in content
    assert "No runs" in content
    assert 'id="lab-replay-grid-stage"' in content
    assert "absolute inset-4" in content
    assert 'id="lab-replay-grid-hud-coord"' in content
    assert 'id="lab-replay-grid-hud-role"' in content
    assert 'id="lab-optimization-replay-attach"' in content
    assert "Attach: —" in content


def test_asteroid_miner_layout_ignores_code_query_string() -> None:
    response = Client().get(
        reverse("web:asteroid-miner-layout"),
        {"code": "SHOULD_NOT_APPEAR_IN_PAGE"},
    )

    assert response.status_code == 200
    assert b"SHOULD_NOT_APPEAR_IN_PAGE" not in response.content


def test_asteroid_miner_layout_post_copy_prg_shows_in_project_page() -> None:
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(create_url, {"copy_code": copy}, follow=True)

    assert response.status_code == 200
    assert copy.encode() in response.content
    assert m.AsteroidProject.objects.count() == 1
    proj = m.AsteroidProject.objects.get()
    assert f"/asteroid-miner-layout/p/{proj.slug}/" in response.request["PATH_INFO"]
    assert m.ReplayFrame.objects.count() >= 6
    ctx = alc.lab_page_context()
    assert ctx["has_replay_frames"] is True
    assert ctx["total_frames"] >= 6
    assert 'id="lab-replay-frames-data"' in response.content.decode()


def test_replay_frame_cell_post_returns_cell_json() -> None:
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy}, follow=False)
    assert create_resp.status_code == 302
    frame = m.ReplayFrame.objects.order_by("frame_index", "id").first()
    assert frame is not None
    track = frame.replay_track
    url = reverse("web:asteroid-miner-layout-replay-frame-cell")
    body = {
        "replay_frame_id": int(frame.pk),
        "replay_track_id": int(track.pk),
        "x": 1,
        "y": 0,
        "project_slug": track.project.slug,
    }
    response = client.post(
        url,
        data=json.dumps(body),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert data["cell"] is not None
    assert data["cell"].get("x") == 1
    assert data["cell"].get("y") == 0
    assert "cell_kind" in data["cell"]


def test_replay_frame_cell_post_wrong_track_403() -> None:
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy}, follow=False)
    assert create_resp.status_code == 302
    frame = m.ReplayFrame.objects.order_by("frame_index", "id").first()
    assert frame is not None
    track = frame.replay_track
    url = reverse("web:asteroid-miner-layout-replay-frame-cell")
    body = {
        "replay_frame_id": int(frame.pk),
        "replay_track_id": int(track.pk) + 99999,
        "x": 1,
        "y": 0,
    }
    response = client.post(
        url,
        data=json.dumps(body),
        content_type="application/json",
    )
    assert response.status_code == 403


def test_replay_frame_cell_post_project_slug_mismatch_403() -> None:
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    create_resp = client.post(create_url, {"copy_code": copy}, follow=False)
    assert create_resp.status_code == 302
    frame = m.ReplayFrame.objects.order_by("frame_index", "id").first()
    assert frame is not None
    track = frame.replay_track
    url = reverse("web:asteroid-miner-layout-replay-frame-cell")
    body = {
        "replay_frame_id": int(frame.pk),
        "replay_track_id": int(track.pk),
        "x": 1,
        "y": 0,
        "project_slug": "wrong-slug-not-this-project",
    }
    response = client.post(
        url,
        data=json.dumps(body),
        content_type="application/json",
    )
    assert response.status_code == 403


def test_asteroid_miner_layout_post_same_copy_dedupes_project() -> None:
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    r1 = client.post(create_url, {"copy_code": copy}, follow=False)
    r2 = client.post(create_url, {"copy_code": copy}, follow=False)
    assert r1.status_code == 302 and r2.status_code == 302

    assert m.AsteroidProject.objects.count() == 1
    proj = m.AsteroidProject.objects.get()
    frames = m.ReplayFrame.objects.filter(replay_track__project_id=proj.pk).order_by("frame_index")
    assert frames.count() >= 6
    assert frames[0].frame_key == "step0_decode_raw"
    assert frames[1].frame_key == "step0_decode"


def test_asteroid_miner_layout_post_project_slug_adds_map_input_to_same_project() -> None:
    client = Client()
    copy1 = _unique_valid_copy()
    copy2 = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    r1 = client.post(create_url, {"copy_code": copy1}, follow=False)
    assert r1.status_code == 302
    proj = m.AsteroidProject.objects.get()
    slug = proj.slug
    r2 = client.post(
        create_url,
        {"copy_code": copy2, "project_slug": slug},
        follow=False,
    )
    assert r2.status_code == 302
    assert m.AsteroidProject.objects.count() == 1
    assert m.AsteroidMapInput.objects.filter(project_id=proj.pk).count() == 2
    page = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert page.status_code == 200
    assert copy2.encode() in page.content


def test_asteroid_miner_layout_create_json_accept_existing_project() -> None:
    """Lab form fetch() uses Accept: application/json; stay on slug with new map input + frames."""
    client = Client()
    copy1 = _unique_valid_copy()
    copy2 = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    r0 = client.post(create_url, {"copy_code": copy1}, follow=False)
    assert r0.status_code == 302
    proj = m.AsteroidProject.objects.get()
    slug = proj.slug
    n_inputs = m.AsteroidMapInput.objects.filter(project_id=proj.pk).count()

    response = client.post(
        create_url,
        {"copy_code": copy2, "project_slug": slug},
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert data["in_place"] is True
    assert data["blueprint_code"] == copy2
    assert len(data.get("lab_replay_frames_json") or []) >= 1
    _assert_optimization_replay_lab_payload(data)
    attach = data.get("optimization_replay_attach")
    assert isinstance(attach, dict)
    assert attach.get("attached") is True
    assert attach.get("reason") == "attached"
    assert data["redirect"] == reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug})
    assert m.AsteroidMapInput.objects.filter(project_id=proj.pk).count() == n_inputs + 1


def test_asteroid_miner_layout_post_rebuilds_replay_when_track_had_no_frames() -> None:
    """Orphan SolverRun+ReplayTrack (0 frames) must recover on re-POST (force retry in view)."""
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    r0 = client.post(create_url, {"copy_code": copy}, follow=False)
    assert r0.status_code == 302
    proj = m.AsteroidProject.objects.get()
    tid = m.ReplayTrack.objects.filter(project=proj).values_list("id", flat=True).first()
    assert tid is not None
    m.ReplayFrame.objects.filter(replay_track_id=tid).delete()
    assert m.ReplayFrame.objects.filter(replay_track_id=tid).count() == 0

    response = client.post(
        create_url,
        {"copy_code": copy},
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert data["replay_ok"] is True
    assert len(data.get("lab_replay_frames_json") or []) >= 5
    _assert_optimization_replay_lab_payload(data)
    attach = data.get("optimization_replay_attach")
    assert isinstance(attach, dict) and attach.get("reason") == "attached"


def test_asteroid_miner_layout_create_json_accept_new_project() -> None:
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(
        create_url,
        {"copy_code": copy},
        HTTP_ACCEPT="application/json",
    )

    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert data["in_place"] is False
    proj = m.AsteroidProject.objects.get()
    expected = reverse("web:asteroid-miner-layout-project", kwargs={"slug": proj.slug})
    assert data["redirect"] == expected
    assert len(data.get("lab_replay_frames_json") or []) >= 5
    _assert_optimization_replay_lab_payload(data)
    attach = data.get("optimization_replay_attach")
    assert isinstance(attach, dict) and attach.get("reason") == "attached"


def test_post_json_optimization_replay_contract_keys() -> None:
    """12E/12I — POST JSON includes optimization replay + attach (no DevTools).

    Read-side ``optimization_replay_diagnostic_reason`` and write-side
    ``optimization_replay_attach.reason`` are separate; do not conflate them.
    """

    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(
        create_url,
        {"copy_code": copy},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    required = {
        "ok",
        "replay_ok",
        "lab_replay_frames_json",
        "lab_ui_initial",
        OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
        "optimization_replay_attach",
    }
    assert required.issubset(data.keys())
    attach = data["optimization_replay_attach"]
    assert isinstance(attach, dict)
    assert "attached" in attach and "reason" in attach
    assert attach["attached"] is True
    assert attach["reason"] == "attached"
    assert "diagnostic" not in attach
    _assert_optimization_replay_lab_payload(data)
    opt = data[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    assert isinstance(opt, dict)
    if attach.get("attached") is True:
        assert int(opt.get("frame_count") or 0) >= 1


@mock.patch(
    "django_apps.web.views.public_pages."
    "run_post_inspection_evolution_and_attach_optimization_replay",
)
def test_post_json_attach_reason_vs_read_diagnostic(mock_attach: mock.MagicMock) -> None:
    """When attach skips, read-side diagnostic may still be ``missing_optimization_replay``."""

    mock_attach.return_value = OptimizationReplayAttachResult(
        attached=False,
        reason="empty_candidate_pool",
    )
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(
        create_url,
        {"copy_code": copy},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    attach = data.get("optimization_replay_attach")
    assert isinstance(attach, dict)
    assert attach["attached"] is False
    assert attach["reason"] == "empty_candidate_pool"
    opt = data[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    assert isinstance(opt, dict)
    assert int(opt.get("frame_count") or 0) == 0
    metrics = opt.get("metrics") or {}
    assert metrics.get("optimization_replay_diagnostic_reason") == "missing_optimization_replay"
    mock_attach.assert_called()
    js = _read_asteroid_lab_js_text()
    assert 'return "Attach: skipped (" + reason + ")"' in js
    assert metrics.get("optimization_replay_diagnostic_reason") != attach.get("reason")


@mock.patch(
    "django_apps.web.views.public_pages."
    "run_post_inspection_evolution_and_attach_optimization_replay",
)
def test_post_json_attach_diagnostic_does_not_overwrite_read_diagnostic(
    mock_attach: mock.MagicMock,
) -> None:
    mock_attach.return_value = OptimizationReplayAttachResult(
        attached=False,
        reason="evolution_failed",
        diagnostic=build_optimization_replay_attach_diagnostic(
            stage="validation",
            validation_passed=False,
        ),
    )
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(
        create_url,
        {"copy_code": copy},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    attach = data.get("optimization_replay_attach")
    assert isinstance(attach, dict)
    assert attach.get("reason") == "evolution_failed"
    assert attach.get("diagnostic", {}).get("stage") == "validation"
    opt = data[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    metrics = opt.get("metrics") or {}
    assert metrics.get("optimization_replay_diagnostic_reason") == "missing_optimization_replay"
    assert "frames" not in attach.get("diagnostic", {})


def test_post_json_attach_true_matches_hud_attached_vocabulary() -> None:
    """12J — attach JSON `{attached: true}` matches HUD ``Attach: attached`` branch in lab JS."""
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(
        create_url,
        {"copy_code": copy},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    attach = data.get("optimization_replay_attach")
    assert attach == {"attached": True, "reason": "attached"}
    js = _read_asteroid_lab_js_text()
    assert 'reason === "attached" ? "Attach: attached"' in js


def test_post_json_attach_skipped_empty_candidate_pool_hud_vocabulary() -> None:
    """12J — skipped attach with reason is a separate write-channel string from read diagnostic."""
    js = _read_asteroid_lab_js_text()
    assert "empty_candidate_pool" in js
    assert 'return "Attach: skipped (" + reason + ")"' in js


def test_post_projects_json_size_attribution_and_optimization_replay_hard_caps() -> None:
    """13A — POST JSON is measurable via test client; optimization replay obeys MAX_REPLAY_*.

    Lab replay uses ``full_map`` / inspection pipeline and is **not** clamped by
    ``MAX_REPLAY_CELLS_PER_FRAME`` (optimization-only constant).
    """

    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(
        create_url,
        {"copy_code": copy},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert_optimization_replay_hard_caps(data)
    lab_n = assert_lab_replay_not_capped_by_optimization_constants(data)
    assert lab_n >= 5
    stats = measure_json_sections(data)
    enc = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert stats["total_bytes"] == len(enc)
    assert stats["lab_replay"]["frame_count"] == lab_n
    assert stats["optimization_replay"]["frame_count"] >= 1
    assert stats["optimization_replay"]["visible_plus_overlay_max"] <= 128
    assert OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY in stats["top_level_key_bytes"]
    assert stats["top_level_key_bytes"]["lab_replay_frames_json"] > 0
    assert stats["top_level_key_bytes"][OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] > 0


def test_asteroid_miner_layout_post_empty_redirects_to_base() -> None:
    client = Client()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    response = client.post(create_url, {"copy_code": ""}, follow=False)

    assert response.status_code == 302
    assert response.url == reverse("web:asteroid-miner-layout")


def test_asteroid_miner_layout_project_unknown_slug_404() -> None:
    response = Client().get(
        reverse("web:asteroid-miner-layout-project", kwargs={"slug": "nonexistent-slug-xyz"}),
    )

    assert response.status_code == 404


def test_asteroid_miner_layout_post_invalid_copy_no_replay_frames() -> None:
    client = Client()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    bad = client.post(create_url, {"copy_code": "not-valid-shapez-payload"}, follow=False)
    assert bad.status_code == 302

    assert m.ReplayFrame.objects.count() == 0


def test_optimization_replay_truncated_badge_visible() -> None:
    html = _lab_html_with_optimization_replay(Client(), _valid_truncated_optimization_track())
    assert 'id="lab-optimization-replay-status"' in html
    assert "Replay status: truncated" in html


def test_optimization_replay_truncation_reason_visible() -> None:
    html = _lab_html_with_optimization_replay(Client(), _valid_truncated_optimization_track())
    assert 'id="lab-optimization-replay-truncation"' in html
    assert "Truncation: cells_reason_xyz" in html


def test_optimization_replay_diagnostic_reason_visible() -> None:
    payload = empty_optimization_replay_track_payload_with_diagnostic(
        "invalid_optimization_replay_payload",
    )
    html = _lab_html_with_optimization_replay(Client(), payload)
    assert "Replay status: fallback-empty" in html
    assert "Diagnostic: invalid_optimization_replay_payload" in html


def test_valid_optimization_replay_hides_diagnostic() -> None:
    html = _lab_html_with_optimization_replay(Client(), _valid_normal_optimization_track())
    assert "Replay status: normal" in html
    assert "Diagnostic:" not in html


def test_empty_replay_without_diagnostic_shows_neutral_state() -> None:
    html = _lab_html_with_optimization_replay(Client(), empty_optimization_replay_track_payload())
    assert "Replay status: fallback-empty" not in html
    assert "Diagnostic:" not in html
    assert "Replay status: truncated" not in html


def test_metadata_hud_does_not_change_replay_controls() -> None:
    html = _lab_html_with_optimization_replay(Client(), _valid_truncated_optimization_track())
    assert 'id="lab-optimization-frame-prev"' in html
    assert 'id="lab-optimization-frame-next"' in html
    assert 'id="lab-optimization-frame-display"' in html


def test_optimization_replay_hud_regression_lab_timeline_controls_present() -> None:
    html = _lab_html_with_optimization_replay(Client(), _valid_normal_optimization_track())
    assert 'id="lab-timeline-play"' in html
    assert 'id="lab-timeline-prev"' in html
    assert 'id="lab-timeline-next"' in html


def test_optimization_replay_malformed_m1_missing_shows_diagnostic_in_html() -> None:
    """12I.4 M1 — missing key classification surfaces as SSR HUD diagnostic."""
    payload = empty_optimization_replay_track_payload_with_diagnostic("missing_optimization_replay")
    html = _lab_html_with_optimization_replay(Client(), payload)
    assert "Replay status: fallback-empty" in html
    assert "Diagnostic: missing_optimization_replay" in html
    assert "Replay status: truncated" not in html


def test_optimization_replay_malformed_m2_empty_list_shows_diagnostic_in_html() -> None:
    """12I.4 M2 — empty list in config maps to empty_optimization_replay_frames."""
    payload = empty_optimization_replay_track_payload_with_diagnostic(
        "empty_optimization_replay_frames"
    )
    html = _lab_html_with_optimization_replay(Client(), payload)
    assert "Replay status: fallback-empty" in html
    assert "Diagnostic: empty_optimization_replay_frames" in html


def test_optimization_replay_malformed_m3_invalid_shape_shows_diagnostic_in_html() -> None:
    """12I.4 M3 — invalid list / frame shape → invalid_optimization_replay_payload."""
    payload = empty_optimization_replay_track_payload_with_diagnostic(
        "invalid_optimization_replay_payload",
    )
    html = _lab_html_with_optimization_replay(Client(), payload)
    assert "Replay status: fallback-empty" in html
    assert "Diagnostic: invalid_optimization_replay_payload" in html


def test_optimization_replay_malformed_m4_truncation_contract_shows_diagnostic_in_html() -> None:
    """12I.4 M4 — replay_truncated / truncation_reason pair break."""
    payload = empty_optimization_replay_track_payload_with_diagnostic("invalid_truncation_contract")
    html = _lab_html_with_optimization_replay(Client(), payload)
    assert "Replay status: fallback-empty" in html
    assert "Diagnostic: invalid_truncation_contract" in html


def test_optimization_replay_malformed_m5_unknown_event_type_shows_diagnostic_in_html() -> None:
    """12I.4 M5 — unsupported event_type string."""
    payload = empty_optimization_replay_track_payload_with_diagnostic(
        "unsupported_or_unknown_event_type",
    )
    html = _lab_html_with_optimization_replay(Client(), payload)
    assert "Replay status: fallback-empty" in html
    assert "Diagnostic: unsupported_or_unknown_event_type" in html


def test_optimization_replay_truncated_hud_preserved_alongside_empty_diagnostic() -> None:
    """Truncation axis + empty diagnostic: SSR matches 12H/12I three-axis layout."""
    html = _lab_html_with_optimization_replay(Client(), _valid_truncated_optimization_track())
    assert "Replay status: truncated" in html
    assert "Truncation: cells_reason_xyz" in html
    assert "Diagnostic:" not in html
