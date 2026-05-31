"""Regression: missing validation_passed must not imply failure when run_success is true."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_orm,
    lab_run_summary_from_solver_summary,
    solver_runs_for_lab_project,
    validation_passed_from_solver_summary,
)

pytestmark = pytest.mark.django_db


def test_validation_passed_explicit_false() -> None:
    assert (
        validation_passed_from_solver_summary(
            {"validation_passed": False, "run_success": True}
        )
        is False
    )


def test_validation_passed_falls_back_to_run_success() -> None:
    assert validation_passed_from_solver_summary({"run_success": True}) is True
    assert validation_passed_from_solver_summary({"run_success": False}) is False
    assert validation_passed_from_solver_summary({}) is False


def test_lab_run_summary_uses_run_success_when_validation_key_missing() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=383,
        status="completed",
        solver_summary={"run_success": True, "stack_run_status": "success"},
    )
    assert row["validation_passed"] is True
    assert row["run_success"] is True


def test_solver_runs_for_lab_project_reads_solver_summary_json_column() -> None:
    project = m.AsteroidProject.objects.create(name="Lab", slug="lab-summary-json")
    m.SolverRun.objects.create(
        project=project,
        run_key="artifact-run",
        status=m.SolverRun.RunStatus.COMPLETED,
        config_json={"artifact_dir": "/tmp/run"},
        solver_summary_json={
            "run_success": True,
            "validation_passed": True,
            "stack_run_status": "success",
        },
    )

    rows = solver_runs_for_lab_project(int(project.pk))

    assert len(rows) == 1
    assert rows[0]["validation_passed"] is True
    assert rows[0]["run_success"] is True


def test_lab_run_summary_from_orm_prefers_solver_summary_json() -> None:
    project = m.AsteroidProject.objects.create(name="ORM", slug="orm-summary-json")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="artifact-run-2",
        status=m.SolverRun.RunStatus.COMPLETED,
        config_json={"solver_summary": {"validation_passed": False}},
        solver_summary_json={"validation_passed": True, "run_success": True},
    )

    row = lab_run_summary_from_orm(run)

    assert row["validation_passed"] is True
