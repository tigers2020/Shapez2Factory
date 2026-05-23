"""Lab map reset — DB clean through inspection replay rebuild."""

from __future__ import annotations

import base64
import gzip
import json

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.lab_map_reset_service import (
    INSPECTION_ALGORITHM_LABEL,
    LabMapResetErrorCode,
    reset_project_map_to_inspection_clean,
)
from django_apps.asteroid_lab.services.project_service import create_project_from_copy_code
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)

pytestmark = pytest.mark.django_db


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _minimal_root(*, version: int = 42) -> dict:
    return {
        "V": version,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }


def test_reset_removes_runtime_solver_run_and_rebuilds_inspection() -> None:
    code = _encode_v4_copy(_minimal_root(version=7))
    dto = create_project_from_copy_code(code, source_label="reset-test")
    base = build_initial_replay_for_map_input(int(dto.map_input_id), overwrite=True)
    assert base.status == "ok"

    create_solver_run(
        int(dto.project_id),
        run_key="runtime-test",
        algorithm_label="runtime_v0",
        config={"marker": True},
    )

    result = reset_project_map_to_inspection_clean(int(dto.project_id))
    assert result.status == "ok"
    assert result.replay_frame_count >= 5

    assert not m.SolverRun.objects.filter(
        project_id=int(dto.project_id),
        algorithm_label="runtime_v0",
    ).exists()
    assert m.SolverRun.objects.filter(
        project_id=int(dto.project_id),
        algorithm_label=INSPECTION_ALGORITHM_LABEL,
    ).exists()
    assert m.ReconstructedAsteroidMap.objects.filter(map_input_id=int(dto.map_input_id)).exists()


def test_reset_requires_map_input() -> None:
    project = m.AsteroidProject.objects.create(name="Empty", slug="reset-no-inp")
    result = reset_project_map_to_inspection_clean(int(project.pk))
    assert result.status == "failed"
    assert result.error_message == LabMapResetErrorCode.NO_MAP_INPUT.value
