"""Integration tests: solver runtime replay timeline wiring (Phase 9F/9G).

Verifies that after Run Solver:
- lab_replay_frames_json contains both reconstruction AND solver phases
- Last frame is result.layout
- frame_index is monotonically 0..n-1
- optimization_replay_* keys are absent
- SolverRun.config_json stores solver_runtime_replay_frames
- ORM ReplayFrame count is unchanged
"""

from __future__ import annotations

import base64
import gzip
import json
import random
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project

pytestmark = pytest.mark.django_db


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _unique_valid_copy() -> str:
    """Minimal asteroid blueprint with actual field evidence (UnknownTile_* = asteroid field)."""
    return _encode_v4_copy(
        {
            "V": random.randint(1, 10_000_000),
            "BP": {
                "$type": "Island",
                "Entries": [
                    # Asteroid field cells (is_asteroid_evidence → true)
                    {"X": 1, "Y": 0, "T": "UnknownTile_A"},
                    {"X": 2, "Y": 0, "T": "UnknownTile_B"},
                    {"X": 3, "Y": 0, "T": "UnknownTile_C"},
                    {"X": 3, "Y": 1, "T": "UnknownTile_D"},
                    # Equipment placed on the field
                    {"X": 2, "Y": 1, "T": "SpaceBelt_Left"},
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


def _seed_minimal_gene_samples(generator_version: str = "exhaustive_sample_gene_v1") -> None:
    genes, _ = generate_exhaustive_sample_genes(
        max_extensions=0, transport_kinds=("belt",), generator_version=generator_version
    )
    assert genes
    g = genes[0]
    m.GeneticSample.objects.update_or_create(
        gene_key=g.key,
        defaults={
            "name": g.name,
            "code": g.encoded_copy_string,
            "metadata_json": dict(g.metadata),
        },
    )


def _run_solver(proj: m.AsteroidProject) -> Any:
    return run_solver_runtime_for_project(int(proj.pk))


# ── Timeline phase content ────────────────────────────────────────────────────


def test_run_solver_timeline_contains_reconstruction_and_solver_phases() -> None:
    """After Run Solver, timeline must include both reconstruction and solver events."""
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    assert result.ok is True
    frames = result.lab_replay_frames_json
    assert len(frames) >= 2

    event_types = [f["event_type"] for f in frames]

    assert (
        ReplayEventType.RECONSTRUCTION_COMPLETED.value in event_types
    ), "reconstruction.completed must be present (Lab ORM)"
    assert (
        ReplayEventType.OPTIMIZATION_INPUT_LOADED.value in event_types
    ), "optimization.input_loaded must be present (solver runtime recorder)"
    assert (
        ReplayEventType.RESULT_LAYOUT.value in event_types
    ), "result.layout must be present (final keyframe)"


def test_run_solver_last_frame_is_result_layout() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    assert result.ok is True
    frames = result.lab_replay_frames_json
    assert frames[-1]["event_type"] == ReplayEventType.RESULT_LAYOUT.value
    assert frames[-1]["phase"] == ReplayPhase.RESULT.value


def test_run_solver_frame_indices_are_monotonic() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    assert result.ok is True
    indices = [f["frame_index"] for f in result.lab_replay_frames_json]
    assert indices == list(range(len(indices)))


def test_run_solver_all_frames_have_renderable_map_view() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    assert result.ok is True
    for frame in result.lab_replay_frames_json:
        mv = frame.get("map_view") or {}
        has_cells = (
            bool(mv.get("full_cells"))
            or bool(mv.get("cell_delta"))
            or bool(mv.get("overlay_cells"))
            or bool(mv.get("base_ref"))
        )
        assert has_cells, f"Frame {frame['event_type']} has empty map_view"


# ── config_json persist ───────────────────────────────────────────────────────


def test_run_solver_persists_runtime_replay_frames_in_config_json() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    assert result.ok is True
    run = m.SolverRun.objects.get(pk=result.solver_run_id)
    assert SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY in run.config_json
    raw = run.config_json[SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY]
    assert isinstance(raw, list) and len(raw) > 0


def test_run_solver_config_json_runtime_frames_last_is_result_layout() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    assert result.ok is True
    run = m.SolverRun.objects.get(pk=result.solver_run_id)
    raw = run.config_json[SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY]
    assert raw[-1]["event_type"] == ReplayEventType.RESULT_LAYOUT.value


# ── ORM immutability ──────────────────────────────────────────────────────────


def test_run_solver_does_not_add_orm_replay_frames() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    before = m.ReplayFrame.objects.filter(replay_track__project=proj).count()
    _run_solver(proj)
    after = m.ReplayFrame.objects.filter(replay_track__project=proj).count()
    assert after == before


# ── result.layout content ─────────────────────────────────────────────────────


def test_run_solver_result_layout_inspector_confirmed_count_matches_summary() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    assert result.ok is True
    if not result.validation_passed:
        pytest.skip("skipping confirmed_count check for failed validation run")

    frames = result.lab_replay_frames_json
    result_frame = frames[-1]
    assert result_frame["event_type"] == ReplayEventType.RESULT_LAYOUT.value

    run_summary = result.solver_summary
    inspector = result_frame.get("inspector") or {}
    assert inspector.get("confirmed_count") == run_summary.get("confirmed_count")
    assert inspector.get("validation_passed") is True


# ── No legacy optimization_replay keys ───────────────────────────────────────


def test_run_solver_response_has_no_optimization_replay_keys() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = _run_solver(proj)

    from django_apps.asteroid_lab.services.solver_runtime_entry import entry_result_to_json_dict

    body = entry_result_to_json_dict(result)
    assert "optimization_replay" not in body
    assert "optimization_replay_attach" not in body
    assert "optimization_replay_read" not in body
