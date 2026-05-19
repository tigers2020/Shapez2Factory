"""Solver runtime HTTP entry service tests (PR8)."""

from __future__ import annotations

import base64
import gzip
import json
import random
from pathlib import Path

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    run_solver_runtime_for_project,
)

pytestmark = pytest.mark.django_db

_GENE_TEMPLATES = (
    Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"
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


def _project_with_map_input() -> m.AsteroidProject:
    client = Client()
    client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": _unique_valid_copy()},
        follow=True,
    )
    return m.AsteroidProject.objects.get()


def test_solver_runtime_entry_persists_replay_and_summary() -> None:
    proj = _project_with_map_input()
    result = run_solver_runtime_for_project(
        int(proj.pk),
        run_key="entry-persist",
        gene_template_path=_GENE_TEMPLATES / "minimal_extractor_e.json",
    )
    assert result.ok is True
    assert result.solver_run_id is not None
    assert result.validation_passed is True

    run = m.SolverRun.objects.get(pk=result.solver_run_id)
    assert SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY in run.config_json
    assert SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY in run.config_json
    assert len(result.lab_replay_frames_json) >= 1
    assert isinstance(result.replay_track_metrics, dict)


def test_solver_runtime_entry_does_not_create_lab_replay_frames() -> None:
    proj = _project_with_map_input()
    lab_count = m.ReplayFrame.objects.filter(replay_track__project=proj).count()
    run_solver_runtime_for_project(
        int(proj.pk),
        gene_template_path=_GENE_TEMPLATES / "minimal_extractor_e.json",
    )
    assert m.ReplayFrame.objects.filter(replay_track__project=proj).count() == lab_count


def test_solver_runtime_entry_requires_map_input() -> None:
    proj = m.AsteroidProject.objects.create(name="Empty", slug="entry-no-inp")
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.NO_MAP_INPUT
