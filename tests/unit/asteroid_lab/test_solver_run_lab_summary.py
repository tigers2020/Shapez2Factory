"""Lab UI solver run summary serialization (read-only)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_orm,
    lab_run_summary_from_solver_summary,
    solver_runs_for_lab_project,
)

pytestmark = pytest.mark.django_db


def test_lab_run_summary_from_solver_summary_failed() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=20,
        status="failed",
        solver_summary={
            "validation_passed": False,
            "confirmed_count": 0,
            "issue_codes": ["orphan_transport", "reserved_path_mismatch"],
        },
    )
    assert row["id"] == "20"
    assert row["status"] == "failed"
    assert row["validation_passed"] is False
    assert row["first_issue_code"] == "orphan_transport"
    assert row["issue_codes"] == ["orphan_transport", "reserved_path_mismatch"]


def test_solver_runs_for_lab_project_orders_newest_first() -> None:
    proj = m.AsteroidProject.objects.create(name="Runs", slug="runs-summary")
    older = m.SolverRun.objects.create(
        project=proj,
        run_key="old",
        algorithm_label="runtime_v0",
        status=m.SolverRun.RunStatus.FAILED,
        config_json={
            SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {
                "validation_passed": False,
                "confirmed_count": 0,
                "issue_codes": ["materialization_failed"],
            }
        },
    )
    newer = m.SolverRun.objects.create(
        project=proj,
        run_key="new",
        algorithm_label="runtime_v0",
        status=m.SolverRun.RunStatus.COMPLETED,
        config_json={
            SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {
                "validation_passed": True,
                "confirmed_count": 2,
                "issue_codes": [],
            }
        },
    )
    rows = solver_runs_for_lab_project(int(proj.pk))
    assert len(rows) == 2
    assert rows[0]["id"] == str(newer.pk)
    assert rows[0]["status"] == "completed"
    assert rows[1]["id"] == str(older.pk)
    assert rows[1]["first_issue_code"] == "materialization_failed"
    assert lab_run_summary_from_orm(older)["status"] == "failed"
