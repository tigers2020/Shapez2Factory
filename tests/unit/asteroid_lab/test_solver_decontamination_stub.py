"""Decontamination: solver entry does not fall back to Layer 02 in-process runtime."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    run_solver_runtime_for_project,
)

pytestmark = pytest.mark.django_db


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=False)
def test_run_solver_ignores_layer02_flag_and_requires_cli_snapshot_payload() -> None:
    project = m.AsteroidProject.objects.create(name="StubOff", slug="stub-off")
    m.AsteroidMapInput.objects.create(project=project, copy_code=_minimal_copy())

    result = run_solver_runtime_for_project(int(project.pk))

    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.SOLVER_SUBPROCESS_FAILED
    assert result.message == "game_data_snapshot payload is required"
