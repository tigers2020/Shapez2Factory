"""PR-A: solver runtime entry is always SOLVER_NOT_AVAILABLE."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SOLVER_NOT_AVAILABLE_MESSAGE,
    SolverRuntimeEntryErrorCode,
    run_solver_runtime_for_project,
)

pytestmark = pytest.mark.django_db


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_run_solver_stub_when_rttp_flag_false() -> None:
    proj = m.AsteroidProject.objects.create(name="StubOff", slug="stub-off")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE
    assert result.message == SOLVER_NOT_AVAILABLE_MESSAGE


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_stub_when_rttp_flag_true() -> None:
    """Setting must not resurrect RTTP after PR-A stub."""
    proj = m.AsteroidProject.objects.create(name="StubOn", slug="stub-on")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        config={"rttp_enabled": True},
    )
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE
    assert result.solver_run_id is None
