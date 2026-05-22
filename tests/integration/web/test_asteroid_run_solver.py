"""HTTP POST run-solver integration tests (PR8)."""

from __future__ import annotations

import base64
import gzip
import json
import random
import re
from pathlib import Path
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.runtime_gene_template_source import GeneTemplateSourceKind
from django_apps.asteroid_lab.services.solver_runtime_entry import SolverRuntimeEntryErrorCode

pytestmark = pytest.mark.django_db

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab"


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
                    {"X": 3, "Y": 1, "T": "Layout_ShapeMinerExtension"},
                ],
            },
        }
    )


# Real layout with mineable rim (equipment bundle regression; commits on HTTP path).
_REGRESSION_COPY_CODE = (
    "SHAPEZ2-4-H4sIAD56CGoA/5yWUUvDMBSF/8vFxwhLsrZbHsU9DBTGlKGMIUEjFmo6khQspf/"
    "drJkgyCT3Umhpe757Tm6akgF2oDiXFYObDagBrkJ/NKBg7Rtt34DB+rW1pxe3OmhQe6jjvdo0O"
    "ry37tMDs13TpBP4D300atulAw4jg5UNrjY+ggM8gbqeM3iOl2j3GE3udN924eXhxN3X1rjVVz"
    "DW19FxZAmQCeCCwRaUvMD9kfN/5RdtqjwXntRldvkzIDFAhjK3M+iWTMAMCVR5QUpkWZlXVi"
    "DKZsxx6pbInTCRJrhA6pH1OU5e4uQLZJjsNLg1TFzCP9iMhC1JVIUZUEmyKEiUxAQTtEZTKI"
    "7IRYolKVCBSEWaxQXCgPQlckxjObKz818DFzhoSYF49r/3EHcttdWu3xk3PZm2MuP4LYAAAw"
    "AZxBUl1ggAAA=="
)


def _regression_copy_code() -> str:
    return _REGRESSION_COPY_CODE


def _project_slug_via_copy(copy: str) -> str:
    client = Client()
    client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": copy},
        follow=True,
    )
    return str(m.AsteroidProject.objects.latest("id").slug)


def _project_slug_via_create() -> str:
    return _project_slug_via_copy(_unique_valid_copy())


def _post_run_solver(slug: str) -> dict[str, Any]:
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    return json.loads(response.content.decode())


def _runs_from_page(content: bytes) -> list[dict[str, Any]]:
    text = content.decode()
    match = re.search(r'<script[^>]+id="lab-runs-data"[^>]*>(.*?)</script>', text, re.DOTALL)
    assert match is not None
    runs = json.loads(match.group(1))
    assert isinstance(runs, list)
    return runs


def _lab_replay_frames_from_page(content: bytes) -> list[dict[str, Any]]:
    text = content.decode()
    match = re.search(
        r'<script[^>]+id="lab-replay-frames-data"[^>]*>(.*?)</script>',
        text,
        re.DOTALL,
    )
    assert match is not None
    return json.loads(match.group(1))


def test_post_run_solver_json_persists_and_returns_payload() -> None:
    slug = _project_slug_via_create()
    data = _post_run_solver(slug)

    assert data["ok"] is True
    assert data["solver_run_id"] is not None
    frames = data.get("lab_replay_frames_json") or []
    assert len(frames) >= 1
    assert isinstance(frames[0].get("map_view"), dict)
    assert isinstance(data.get("replay_track_metrics"), dict)
    assert isinstance(data.get("solver_summary"), dict)
    summary = data["solver_summary"]
    assert "capacity_satisfied" in summary
    assert "capacity_deficit_count" in summary
    assert "throughput_deficit_count" in summary
    assert "placement_capacity_satisfied" in summary
    assert "throughput_budget_satisfied" in summary
    assert "target_placement_count" in summary
    assert "run_success" in summary
    assert data["validation_passed"] is True
    assert data["validation_issue_codes"] == []
    assert data["validation_issue_details"] == []
    assert isinstance(data.get("run_summary"), dict)
    assert "connected" not in data["run_summary"]
    assert "placed" in data["run_summary"]
    assert data["run_summary"]["id"] == str(data["solver_run_id"])
    run_summary = data["run_summary"]
    if summary.get("run_success"):
        assert run_summary["status"] == "completed"
    elif summary.get("validation_passed"):
        assert run_summary["status"] == "partial"
    else:
        assert run_summary["status"] == "failed"
    assert "capacity_satisfied" in run_summary
    assert "run_success" in run_summary
    assert "optimization_replay_attach" not in data
    assert "optimization_replay_read" not in data
    _assert_frames_have_js_renderable_cells(frames)

    src = data.get("gene_template_source")
    assert isinstance(src, dict)
    assert src["source"] == GeneTemplateSourceKind.GENETIC_SAMPLE_DB.value
    assert src["gene_count"] >= 1


def _assert_frames_have_js_renderable_cells(frames: list[dict]) -> None:
    """At least one timeline frame must expose lab x != 0 or overlay/delta cells."""

    for frame in frames:
        mv = frame.get("map_view")
        if not isinstance(mv, dict):
            continue
        for key in ("full_cells", "overlay_cells", "cell_delta"):
            cells = mv.get(key)
            if not isinstance(cells, list):
                continue
            for cell in cells:
                if isinstance(cell, dict) and cell.get("x") not in (None, 0):
                    return
    msg = "expected at least one map_view cell with non-zero lab x for grid render"
    raise AssertionError(msg)


def test_post_run_solver_validation_passes_for_basic_asteroid() -> None:
    slug = _project_slug_via_copy(_regression_copy_code())
    data = _post_run_solver(slug)

    assert data["ok"] is True
    _assert_frames_have_js_renderable_cells(data.get("lab_replay_frames_json") or [])
    assert data["validation_passed"] is True
    issue_codes = list(data["validation_issue_codes"])
    assert all(code != "materialization_failed" for code in issue_codes)
    assert data["validation_issue_details"] == []

    summary = data["solver_summary"]
    run = data["run_summary"]
    if summary.get("run_success"):
        assert run["status"] == "completed"
    elif summary.get("validation_passed"):
        assert run["status"] == "partial"
    else:
        assert run["status"] == "failed"
    assert run["validation_passed"] is True
    assert "capacity_satisfied" in run
    assert "placement_capacity_satisfied" in run
    assert "throughput_budget_satisfied" in run
    assert "run_success" in run
    if not summary.get("run_success") and summary.get("validation_passed"):
        assert summary.get("placement_capacity_satisfied") is False or (
            summary.get("throughput_budget_satisfied") is False
        )
        assert run["run_success"] is False
    assert run["placed"] == summary["confirmed_count"]
    assert run["placed"] > 0
    assert "connected" not in run

    summary = data["solver_summary"]
    assert summary["validation_passed"] is True
    assert int(summary.get("confirmed_count") or 0) > 0


def test_post_run_solver_unknown_slug_404() -> None:
    url = reverse(
        "web:asteroid-miner-layout-project-run-solver",
        kwargs={"slug": "nonexistent-slug-xyz"},
    )
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 404
    data = json.loads(response.content.decode())
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND.value
    assert data["lab_replay_frames_json"] == []


def test_post_run_solver_no_map_input_400() -> None:
    proj = m.AsteroidProject.objects.create(name="Empty", slug="run-solver-empty")
    url = reverse(
        "web:asteroid-miner-layout-project-run-solver",
        kwargs={"slug": proj.slug},
    )
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 400
    data = json.loads(response.content.decode())
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.NO_MAP_INPUT.value


def test_get_project_page_includes_composed_replay_after_run() -> None:
    slug = _project_slug_via_create()
    _post_run_solver(slug)

    page = Client().get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert page.status_code == 200
    assert b'id="lab-replay-frames-data"' in page.content
    assert b"lab-optimization-replay-data" not in page.content


def test_get_project_page_lists_solver_runs_after_run() -> None:
    slug = _project_slug_via_copy(_regression_copy_code())
    data = _post_run_solver(slug)

    page = Client().get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert page.status_code == 200
    text = page.content.decode()
    assert 'data-lab-run-id="' in text

    runs = _runs_from_page(page.content)
    assert len(runs) >= 1
    latest = runs[0]
    assert latest["id"] is not None
    assert latest["id"] == str(data["solver_run_id"])
    summary = data["solver_summary"]
    if summary.get("run_success"):
        assert latest["status"] == "completed"
    elif summary.get("validation_passed"):
        assert latest["status"] == "partial"
    else:
        assert latest["status"] == "failed"
    assert latest["validation_passed"] is True
    if summary.get("run_success"):
        assert latest.get("first_issue_code") in (None, "")
    assert "connected" not in latest
    assert "placed" in latest
    assert latest["placed"] == data["solver_summary"]["confirmed_count"]
    assert latest["placed"] > 0


def test_post_run_solver_json_updates_page_context_timeline() -> None:
    slug = _project_slug_via_create()
    _post_run_solver(slug)

    page = Client().get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    frames = _lab_replay_frames_from_page(page.content)
    assert len(frames) >= 1
    assert isinstance(frames[0].get("map_view"), dict)


@pytest.mark.django_db
def test_post_run_solver_no_gene_templates_in_db_400() -> None:
    """If DB has no gene templates, run-solver returns 400 with NO_GENE_TEMPLATES_IN_DB."""
    m.GeneticSample.objects.all().delete()
    slug = _project_slug_via_create()
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 400
    data = json.loads(response.content.decode())
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.NO_GENE_TEMPLATES_IN_DB.value
