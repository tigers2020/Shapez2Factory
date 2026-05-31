"""Regression: missing validation_passed must not imply failure when run_success is true."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_06_COMMIT_VALIDATE,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_orm,
    lab_run_summary_from_solver_summary,
    solver_runs_for_lab_project,
    validation_passed_from_solver_summary,
)

pytestmark = pytest.mark.django_db


def test_validation_passed_explicit_false() -> None:
    assert (
        validation_passed_from_solver_summary({"validation_passed": False, "run_success": True})
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


def test_layer_outcomes_derive_completed_slugs_from_layer_summaries() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=389,
        status="completed",
        solver_summary={
            "stack_run_status": "success",
            "validation_passed": False,
            "run_success": True,
            "reconstruction_capacity": {"shape_field_cell_count": 583},
            "layer_summaries": [
                {
                    "layer_slug": LAYER_02_EXTERIOR_TRANSPORT,
                    "outcome": "completed",
                    "metrics": {},
                },
                {
                    "layer_slug": LAYER_03_RIM_GREEDY_PLACEMENT,
                    "outcome": "completed",
                    "metrics": {},
                },
                {
                    "layer_slug": LAYER_06_COMMIT_VALIDATE,
                    "outcome": "completed",
                    "metrics": {},
                },
            ],
        },
    )
    layers = {layer["layer_slug"]: layer for layer in row["layer_summaries"]}
    assert layers[LAYER_02_EXTERIOR_TRANSPORT]["outcome"] == "completed"
    assert layers[LAYER_03_RIM_GREEDY_PLACEMENT]["outcome"] == "completed"
    assert layers[LAYER_06_COMMIT_VALIDATE]["outcome"] == "failed"


def test_layer02_highlights_read_shortfall_metrics_from_cli_layer_summaries() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=2,
        status="completed",
        solver_summary={
            "stack_run_status": "success",
            "completed_layer_slugs": [LAYER_02_EXTERIOR_TRANSPORT],
            "layer_summaries": [
                {
                    "layer_slug": LAYER_02_EXTERIOR_TRANSPORT,
                    "outcome": "completed",
                    "metrics": {
                        "required_connector_count": 866,
                        "required_planned_count": 120,
                        "planned_connector_count": 120,
                        "candidate_slot_count": 120,
                        "connector_shortfall_count": 746,
                        "unmet_reason": "insufficient_connector_sites",
                    },
                }
            ],
        },
    )
    layers = {layer["layer_slug"]: layer for layer in row["layer_summaries"]}
    l2 = layers[LAYER_02_EXTERIOR_TRANSPORT]
    labels = {item["label"]: item["value"] for item in l2["highlights"]}
    assert labels["Required planned"] == "120"
    assert labels["Planned connectors"] == "120"
    assert labels["Candidate slots"] == "120"
    assert labels["Connector shortfall"] == "746"
    assert labels["Unmet reason"] == "insufficient_connector_sites"


def test_layer03_highlights_read_nested_cli_layer_summaries() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=1,
        status="completed",
        solver_summary={
            "stack_run_status": "success",
            "completed_layer_slugs": [LAYER_03_RIM_GREEDY_PLACEMENT],
            "layer_summaries": [
                {
                    "layer_slug": LAYER_03_RIM_GREEDY_PLACEMENT,
                    "outcome": "completed",
                    "metrics": {
                        "rim_anchor_count": 81,
                        "committed_placement_count": 0,
                        "rejected_attempt_count": 12,
                        "layer_skip_reason": "no_route_goals",
                        "winning_variant_id": "",
                    },
                }
            ],
        },
    )
    layers = {layer["layer_slug"]: layer for layer in row["layer_summaries"]}
    l3 = layers[LAYER_03_RIM_GREEDY_PLACEMENT]
    labels = {item["label"]: item["value"] for item in l3["highlights"]}
    assert labels["Rim anchor slots"] == "81"
    assert labels["Committed placements"] == "0"
    assert labels["Rejected attempts"] == "12"
    assert labels["Layer skip reason"] == "no_route_goals"


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
