"""Integration tests for 13C2-lite compose-once + persisted replay cache."""

from __future__ import annotations

import base64
import gzip
import json
import random
from unittest.mock import patch

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services import lab_replay_timeline_payload as lrtp
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    is_cache_summary_valid,
    load_composed_frames_for_run_id,
    load_manifest_summary_for_run_id,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
    SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY,
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)
from tests.support.measure_json_sections import measure_json_sections

pytestmark = pytest.mark.django_db

_LAYER02_COMPOSE_PATCH = (
    "django_apps.asteroid_lab.services.solver_runtime_layer02.build_lab_replay_frames_for_project"
)
_COMPOSE_ENTRY_PATCH = (
    "django_apps.asteroid_lab.services.solver_runtime_entry.build_lab_replay_frames_for_project"
)
_PAGE_CONTEXT_COMPOSE_PATCH = (
    "django_apps.web.services.asteroid_lab_page_context.build_lab_replay_frames_for_project"
)
_PAGE_COMPOSED_LOAD_PATCH = (
    "django_apps.asteroid_lab.services.lab_replay_persisted_cache.load_composed_frames_for_run_id"
)
_GET_COMPOSE_PATCH = (
    "django_apps.web.views.public_pages.build_lab_replay_frames_for_project"
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    return imported_game_data_batch_module


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(text)).decode("ascii")
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


def _client_run_solver(client: Client) -> tuple[str, int, m.AsteroidProject]:
    create_resp = client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": _unique_valid_copy()},
        HTTP_ACCEPT="application/json",
    )
    assert create_resp.status_code == 200
    slug = json.loads(create_resp.content.decode())["project_slug"]
    proj = m.AsteroidProject.objects.get(slug=slug)
    run_body = json.loads(
        client.post(
            reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug}),
            HTTP_ACCEPT="application/json",
        ).content.decode()
    )
    assert run_body.get("solver_run_id") is not None
    return slug, int(run_body["solver_run_id"]), proj


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_run_solver_persists_composed_replay_cache() -> None:
    proj = m.AsteroidProject.objects.create(name="ComposeDefer", slug="compose-defer-proj")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        config={"throughput_target_percent": 80},
    )
    assert result.ok is True
    assert result.solver_run_id is not None
    run_id = int(result.solver_run_id)

    frames = load_composed_frames_for_run_id(run_id)
    summary = load_manifest_summary_for_run_id(run_id)
    assert frames is not None
    assert len(frames) >= 1
    assert is_cache_summary_valid(summary)
    assert summary is not None
    assert summary["frame_count"] == len(frames)

    run = m.SolverRun.objects.get(pk=run_id)
    config = dict(run.config_json or {})
    runtime_frames = config.get(SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY)
    assert isinstance(runtime_frames, list)
    assert len(runtime_frames) >= 1
    assert isinstance(config.get(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY), dict)
    assert isinstance(config.get(SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY), list)


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_run_solver_layer02_composer_called_once_on_success() -> None:
    proj = m.AsteroidProject.objects.create(name="ComposeOnce", slug="compose-once-proj")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    with patch(
        _LAYER02_COMPOSE_PATCH,
        wraps=lrtp.build_lab_replay_frames_for_project,
    ) as compose_mock:
        result = run_solver_runtime_for_project(
            int(proj.pk),
            config={"throughput_target_percent": 80},
        )
    assert result.ok is True
    assert compose_mock.call_count == 1
    _args, kwargs = compose_mock.call_args
    assert kwargs.get("solver_run_id") == int(result.solver_run_id)


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_run_solver_invalid_throughput_still_composes_without_persist_cache() -> None:
    """Error path E1: compose allowed; no successful run → no composed cache keys."""
    proj = m.AsteroidProject.objects.create(name="ComposeErr", slug="compose-err-pct")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    empty_metrics = {
        "frame_count": 0,
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": None,
    }
    with patch(_LAYER02_COMPOSE_PATCH, return_value=([], empty_metrics)) as compose_mock:
        result = run_solver_runtime_for_project(
            int(proj.pk),
            config={"throughput_target_percent": 0},
        )
    assert result.ok is False
    assert compose_mock.call_count == 1
    assert result.solver_run_id is None


@override_settings(
    ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True,
    ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy",
)
def test_entry_result_lazy_uses_persisted_summary_without_recompose() -> None:
    proj = m.AsteroidProject.objects.create(name="EntrySummary", slug="entry-summary-proj")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        config={"throughput_target_percent": 80},
    )
    assert result.ok is True
    assert result.solver_run_id is not None

    with patch(_COMPOSE_ENTRY_PATCH) as compose_mock:
        body = entry_result_to_json_dict(result, project_slug=str(proj.slug))

    assert compose_mock.call_count == 0
    lab_replay = body.get("lab_replay") or {}
    assert lab_replay.get("mode") == "lazy"
    assert lab_replay.get("frame_count", 0) >= 1
    assert lab_replay.get("preview_frame") is not None
    assert isinstance(lab_replay.get("fetch_url"), str)
    assert "lab_replay_frames_json" not in body
    sections = measure_json_sections(body)
    assert int(sections["total_bytes"]) > 0


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_cache_hit_no_compose(client: Client) -> None:
    slug, _run_id, _proj = _client_run_solver(client)
    with patch(_PAGE_CONTEXT_COMPOSE_PATCH) as compose_mock:
        resp = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert resp.status_code == 200
    assert compose_mock.call_count == 0
    html = resp.content.decode()
    assert 'id="lab-replay-manifest-data"' in html
    assert 'id="lab-replay-frames-data"' not in html


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_ssr_does_not_load_composed_frames_blob(client: Client) -> None:
    slug, _run_id, _proj = _client_run_solver(client)
    with patch(
        _PAGE_COMPOSED_LOAD_PATCH,
        side_effect=AssertionError("composed frames loader must not run on SSR"),
    ):
        resp = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert resp.status_code == 200


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_project_page_lazy_cache_miss_backfills_summary(client: Client) -> None:
    slug, run_id, _proj = _client_run_solver(client)
    run = m.SolverRun.objects.get(pk=run_id)
    config = dict(run.config_json or {})
    config.pop(SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY, None)
    config.pop(SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY, None)
    run.config_json = config
    run.save(update_fields=["config_json"])
    with patch(
        _PAGE_CONTEXT_COMPOSE_PATCH,
        wraps=lrtp.build_lab_replay_frames_for_project,
    ) as compose_mock:
        resp = client.get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert resp.status_code == 200
    assert compose_mock.call_count == 1
    assert is_cache_summary_valid(load_manifest_summary_for_run_id(run_id))


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_lab_replay_get_uses_persisted_artifact_when_available(client: Client) -> None:
    slug, run_id, _proj = _client_run_solver(client)
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": run_id},
    )
    with patch(_GET_COMPOSE_PATCH) as compose_mock:
        resp = client.get(url)
    assert resp.status_code == 200
    assert compose_mock.call_count == 0
    data = json.loads(resp.content.decode())
    assert data["frame_count"] == len(data["frames"])
    assert data["frame_count"] >= 1


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_lab_replay_get_falls_back_to_compose_without_artifact(client: Client) -> None:
    slug, run_id, _proj = _client_run_solver(client)
    run = m.SolverRun.objects.get(pk=run_id)
    config = dict(run.config_json or {})
    config.pop(SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY, None)
    config.pop(SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY, None)
    run.config_json = config
    run.save(update_fields=["config_json"])
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": run_id},
    )
    with patch(
        _GET_COMPOSE_PATCH,
        wraps=lrtp.build_lab_replay_frames_for_project,
    ) as compose_mock:
        resp = client.get(url)
    assert resp.status_code == 200
    assert compose_mock.call_count == 1
    assert is_cache_summary_valid(load_manifest_summary_for_run_id(run_id))


@override_settings(ASTEROID_LAB_REPLAY_PAYLOAD_MODE="lazy")
def test_lazy_get_semantic_equivalence_persisted_vs_compose(client: Client) -> None:
    slug, run_id, _proj = _client_run_solver(client)
    persisted = load_composed_frames_for_run_id(run_id)
    assert persisted is not None
    run = m.SolverRun.objects.get(pk=run_id)
    config = dict(run.config_json or {})
    config.pop(SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY, None)
    config.pop(SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY, None)
    run.config_json = config
    run.save(update_fields=["config_json"])
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": slug, "run_id": run_id},
    )
    resp = client.get(url)
    fallback = json.loads(resp.content.decode())["frames"]
    assert json.dumps(persisted, sort_keys=True) == json.dumps(fallback, sort_keys=True)
