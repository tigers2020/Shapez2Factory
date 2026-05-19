"""PR7 solver button pipeline integration tests (orchestration + persist, no HTTP)."""

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
from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    LoadedReconstructionSnapshot,
    loaded_reconstruction_snapshot_from_result,
)
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    persist_optimization_replay_frames_to_solver_run,
)
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    deserialize_optimization_replay_frames_from_json,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.optimization.gene_template_loader import load_gene_templates_from_json
from django_apps.asteroid_lab.services.solver_runtime_pipeline import run_solver_runtime_pipeline

pytestmark = pytest.mark.django_db

_GENE_TEMPLATES = (
    Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"
)

_MINIMAL_GENE_TEMPLATES = load_gene_templates_from_json(_GENE_TEMPLATES / "minimal_extractor_e.json")


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


def _project_with_reconstruction() -> tuple[m.AsteroidProject, LoadedReconstructionSnapshot]:
    client = Client()
    copy = _unique_valid_copy()
    client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": copy},
        follow=True,
    )
    proj = m.AsteroidProject.objects.get()
    inp = m.AsteroidMapInput.objects.filter(project=proj).order_by("-id").first()
    assert inp is not None
    _cleanup, recon = run_reconstruction_for_map_input(int(inp.pk))
    loaded = loaded_reconstruction_snapshot_from_result(recon)
    return proj, loaded


def test_solver_button_pipeline_persists_result() -> None:
    proj, loaded = _project_with_reconstruction()
    run_dto = create_solver_run(
        int(proj.pk),
        run_key="pr7-persist",
        algorithm_label="runtime_v0",
        config={"seed_flag": True},
    )
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_MINIMAL_GENE_TEMPLATES,
        run_key="pr7-persist",
    )
    attach = persist_optimization_replay_frames_to_solver_run(
        run_dto.id,
        result.replay_frames,
        solver_summary=result.solver_summary,
        server_xy_params=loaded.server_xy_params,
    )
    assert attach.attached is True

    run = m.SolverRun.objects.get(pk=run_dto.id)
    assert run.config_json.get("seed_flag") is True
    assert SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY in run.config_json
    assert SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY in run.config_json
    assert isinstance(run.config_json[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY], dict)


def test_solver_button_pipeline_emits_replay_events() -> None:
    _proj, loaded = _project_with_reconstruction()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_MINIMAL_GENE_TEMPLATES,
    )
    seq = [f.event_type for f in result.replay_frames]
    required = {
        OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        OptimizationReplayEventType.VALIDATION_COMPLETED,
        OptimizationReplayEventType.ROUTE_MATERIALIZED,
    }
    assert required.issubset(set(seq))

    raw = [f.to_json_dict() for f in result.replay_frames]
    restored = deserialize_optimization_replay_frames_from_json(raw)
    assert restored is not None
    assert [f.event_type for f in restored] == seq

    result2 = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_MINIMAL_GENE_TEMPLATES,
    )
    assert [f.event_type for f in result2.replay_frames] == seq


def test_solver_button_pipeline_validation_read_only() -> None:
    _proj, loaded = _project_with_reconstruction()
    cells_before = loaded.cells

    r1 = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_MINIMAL_GENE_TEMPLATES,
    )
    r2 = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_MINIMAL_GENE_TEMPLATES,
    )

    assert loaded.cells == cells_before
    assert r1.commit == r2.commit
    assert r1.validation == r2.validation


def test_solver_button_pipeline_no_implicit_lab_optimization_sync() -> None:
    proj, loaded = _project_with_reconstruction()
    lab_frame_count = m.ReplayFrame.objects.filter(replay_track__project=proj).count()
    lab_frames = list(
        m.ReplayFrame.objects.filter(replay_track__project=proj).values_list("id", "frame_index")
    )

    run_dto = create_solver_run(
        int(proj.pk),
        run_key="pr7-lab-sync",
        algorithm_label="runtime_v0",
        config={},
    )
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_MINIMAL_GENE_TEMPLATES,
    )
    persist_optimization_replay_frames_to_solver_run(
        run_dto.id,
        result.replay_frames,
        solver_summary=result.solver_summary,
        server_xy_params=loaded.server_xy_params,
    )

    assert m.ReplayFrame.objects.filter(replay_track__project=proj).count() == lab_frame_count
    assert (
        list(
            m.ReplayFrame.objects.filter(replay_track__project=proj).values_list(
                "id", "frame_index"
            )
        )
        == lab_frames
    )

    run = m.SolverRun.objects.get(pk=run_dto.id)
    assert SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY in run.config_json
