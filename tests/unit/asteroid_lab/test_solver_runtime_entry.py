"""Solver runtime entry stub tests (optimization pipeline removed)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SOLVER_NOT_AVAILABLE_MESSAGE,
    SolverRuntimeEntryErrorCode,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)

pytestmark = pytest.mark.django_db


def test_solver_runtime_entry_requires_map_input() -> None:
    proj = m.AsteroidProject.objects.create(name="Empty", slug="entry-no-inp")
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.NO_MAP_INPUT


def test_solver_runtime_entry_returns_solver_not_available_when_map_input_exists() -> None:
    proj = m.AsteroidProject.objects.create(name="Lab", slug="entry-stub")
    m.AsteroidMapInput.objects.create(project=proj, copy_code="SHAPEZ2-4-e30=")
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE
    assert result.message == SOLVER_NOT_AVAILABLE_MESSAGE


def test_entry_result_to_json_dict_includes_error_code_and_message() -> None:
    proj = m.AsteroidProject.objects.create(name="Lab2", slug="entry-stub-json")
    m.AsteroidMapInput.objects.create(project=proj, copy_code="SHAPEZ2-4-e30=")
    result = run_solver_runtime_for_project(int(proj.pk))
    body = entry_result_to_json_dict(result)
    assert body["ok"] is False
    assert body["error_code"] == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value
    assert body["message"] == SOLVER_NOT_AVAILABLE_MESSAGE
