import base64
import gzip
import json
import random

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.web.services import asteroid_lab_page_context as alc

pytestmark = pytest.mark.django_db


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
    client.post(create_url, {"copy_code": copy}, follow=True)
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
    client.post(create_url, {"copy_code": copy}, follow=True)
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
    client.post(create_url, {"copy_code": copy}, follow=True)
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
    client.post(create_url, {"copy_code": copy}, follow=True)
    client.post(create_url, {"copy_code": copy}, follow=True)

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
    client.post(create_url, {"copy_code": copy1}, follow=True)
    proj = m.AsteroidProject.objects.get()
    slug = proj.slug
    client.post(
        create_url,
        {"copy_code": copy2, "project_slug": slug},
        follow=True,
    )
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
    client.post(create_url, {"copy_code": copy1}, follow=True)
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
    assert data["redirect"] == reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug})
    assert m.AsteroidMapInput.objects.filter(project_id=proj.pk).count() == n_inputs + 1


def test_asteroid_miner_layout_post_rebuilds_replay_when_track_had_no_frames() -> None:
    """Orphan SolverRun+ReplayTrack (0 frames) must recover on re-POST (force retry in view)."""
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    client.post(create_url, {"copy_code": copy}, follow=True)
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


def test_asteroid_miner_layout_run_solver_appends_optimization_frames() -> None:
    client = Client()
    copy = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    client.post(create_url, {"copy_code": copy}, follow=True)
    proj = m.AsteroidProject.objects.get()
    tid = m.ReplayTrack.objects.filter(project=proj).values_list("id", flat=True).first()
    mid = m.AsteroidMapInput.objects.filter(project=proj).values_list("id", flat=True).first()
    assert tid is not None and mid is not None
    n_before = m.ReplayFrame.objects.filter(replay_track_id=tid).count()
    url = reverse("web:asteroid-miner-layout-run-solver")
    body = {
        "project_slug": proj.slug,
        "replay_track_id": int(tid),
        "map_input_id": int(mid),
    }
    response = client.post(
        url,
        data=json.dumps(body),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    appended = int(data["appended_optimization_frames"])
    assert appended > 0
    assert int(data["inspection_frame_count_before"]) == n_before
    frames = data.get("lab_replay_frames_json") or []
    assert len(frames) == n_before + appended
    last = frames[-1]
    assert int(last["frame_index"]) == len(frames) - 1
    assert str(last["frame_key"]).startswith("optimization_")
    assert last["phase"] == "optimization"


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
    client.post(create_url, {"copy_code": "not-valid-shapez-payload"}, follow=True)

    assert m.ReplayFrame.objects.count() == 0
