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
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import SolverRuntimeEntryErrorCode

pytestmark = pytest.mark.django_db

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab"


@pytest.fixture(autouse=True)
def seed_gene_templates_db() -> None:
    """Seed minimal GeneticSample rows so Run Solver DB resolver can load templates."""
    genes, _ = generate_exhaustive_sample_genes(
        max_extensions=0, transport_kinds=("belt",), generator_version="exhaustive_sample_gene_v1"
    )
    for g in genes:
        m.GeneticSample.objects.update_or_create(
            gene_key=g.key,
            defaults={
                "name": g.name,
                "code": g.encoded_copy_string,
                "metadata_json": dict(g.metadata),
            },
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


def _frames_by_event(frames: list[dict[str, Any]], event_type: str) -> list[dict[str, Any]]:
    return [f for f in frames if f.get("event_type") == event_type]


_PLACEMENT_OVERLAY_KINDS = frozenset(
    {
        "shape_miner",
        "fluid_miner",
        "shape_miner_extension",
        "fluid_miner_extension",
        "space_belt",
        "space_pipe",
    }
)


def _assert_validation_completed_has_placement_overlays(frames: list[dict[str, Any]]) -> None:
    val_frames = _frames_by_event(frames, "validation.completed")
    assert len(val_frames) == 1, "expected exactly one validation.completed frame"
    mv = val_frames[0].get("map_view")
    assert isinstance(mv, dict), "validation.completed must expose map_view"
    overlay = mv.get("overlay_cells")
    assert (
        isinstance(overlay, list) and overlay
    ), "validation.completed map_view.overlay_cells must be non-empty when commits exist"
    placement = [
        c
        for c in overlay
        if isinstance(c, dict)
        and isinstance(c.get("kind"), str)
        and c["kind"] in _PLACEMENT_OVERLAY_KINDS
        and isinstance(c.get("x"), int)
        and isinstance(c.get("y"), int)
    ]
    assert placement, (
        "validation.completed overlay must include at least one projected placement cell "
        f"(kinds {_PLACEMENT_OVERLAY_KINDS!r})"
    )
    # Transport overlay cells must carry tile_type + sprite_identifier for front sprite lookup.
    transport_cells = [c for c in placement if c["kind"] in ("space_belt", "space_pipe")]
    for tc in transport_cells:
        assert isinstance(tc.get("tile_type"), str) and tc["tile_type"], (
            f"transport overlay cell missing tile_type: {tc!r}"
        )
        assert tc.get("sprite_identifier") == tc["tile_type"], (
            f"sprite_identifier must equal tile_type in wire JSON: {tc!r}"
        )


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
    assert data["validation_passed"] is True
    assert data["validation_issue_codes"] == []
    assert data["validation_issue_details"] == []
    assert isinstance(data.get("run_summary"), dict)
    assert "connected" not in data["run_summary"]
    assert "placed" in data["run_summary"]
    assert data["run_summary"]["id"] == str(data["solver_run_id"])
    assert data["run_summary"]["status"] == "completed"
    assert data["optimization_replay_attach"]["attached"] is True
    assert data["optimization_replay_attach"]["reason"] == "attached"
    assert isinstance(data.get("optimization_replay_read"), dict)
    _assert_frames_have_js_renderable_cells(frames)

    src = data.get("gene_template_source")
    assert isinstance(src, dict)
    assert src["source"] == GeneTemplateSourceKind.GENETIC_SAMPLE_DB.value
    assert src["gene_count"] >= 1


def _assert_frames_have_js_renderable_cells(frames: list[dict]) -> None:
    """At least one unified frame must expose lab x != 0 or overlay/delta cells."""

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
    assert data["validation_issue_codes"] == []
    assert data["validation_issue_details"] == []

    summary = data["solver_summary"]
    run = data["run_summary"]
    assert run["status"] == "completed"
    assert run["validation_passed"] is True
    assert run["placed"] == summary["confirmed_count"]
    assert run["placed"] > 0
    assert "connected" not in run

    frames = data.get("lab_replay_frames_json") or []
    _assert_validation_completed_has_placement_overlays(frames)
    val_metrics = _frames_by_event(frames, "validation.completed")[0]["metrics"]
    assert val_metrics["passed"] is True
    assert val_metrics.get("issue_codes") == []
    assert val_metrics.get("first_issue_code") in (None, "")

    route_frames = _frames_by_event(frames, "route.committed")
    assert route_frames
    for frame in route_frames:
        route_metrics = frame["metrics"]
        assert route_metrics["path_contains_output_stub"] is True
        assert route_metrics["path_len"] >= 1
        assert route_metrics["reserved_cell_count"] >= route_metrics["path_len"]
        assert route_metrics["path_head"] == route_metrics["output_stub"]


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
    assert latest["status"] == "completed"
    assert latest["validation_passed"] is True
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
def test_post_run_solver_no_gene_templates_in_db_400(seed_gene_templates_db: None) -> None:
    """If DB has no gene templates, run-solver returns 400 with NO_GENE_TEMPLATES_IN_DB."""
    m.GeneticSample.objects.all().delete()
    slug = _project_slug_via_create()
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 400
    data = json.loads(response.content.decode())
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.NO_GENE_TEMPLATES_IN_DB.value
