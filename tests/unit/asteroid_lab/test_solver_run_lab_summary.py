"""Lab UI solver run summary serialization (read-only)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_config_keys import (
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
    assert "connected" not in row
    assert row["placed"] == 0
    assert row["first_issue_detail"] is None


def test_lab_run_summary_capacity_fields_partial() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=64,
        status="partial",
        solver_summary={
            "validation_passed": True,
            "capacity_satisfied": False,
            "run_success": False,
            "placement_capacity_satisfied": False,
            "throughput_budget_satisfied": True,
            "confirmed_count": 6,
            "confirmed_throughput": 96,
            "target_miner_bundle_count": 84,
            "target_placement_count": 84,
            "target_throughput": 84,
            "capacity_deficit_count": 78,
            "throughput_deficit_count": 0,
            "issue_codes": ["under_target_throughput"],
        },
    )
    assert row["status"] == "partial"
    assert row["validation_passed"] is True
    assert row["capacity_satisfied"] is False
    assert row["run_success"] is False
    assert row["placement_capacity_satisfied"] is False
    assert row["throughput_budget_satisfied"] is True
    assert row["target_miner_bundle_count"] == 84
    assert row["target_placement_count"] == 84
    assert row["target_throughput"] == 84
    assert row["confirmed_throughput"] == 96
    assert row["capacity_deficit_count"] == 78
    assert row["throughput_deficit_count"] == 0
    assert row["placed"] == 6


def test_lab_run_summary_nested_capacity_from_solver_summary() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=99,
        status="completed",
        solver_summary={
            "validation_passed": True,
            "confirmed_count": 1,
            "reconstruction_observability": {
                "cell_count": 10,
                "display_cell_count": 120,
                "mineable_cell_count": 40,
                "confirmed_cell_count": 8,
                "shape_confirmed_cell_count": 8,
                "fluid_confirmed_cell_count": 0,
                "primary_resource_kind": "shape",
                "ambiguous_cell_count": 1,
                "external_void_cell_count": 1,
                "quality_tier": "CONFIDENT_RECONSTRUCTION",
                "confidence_score": "0.9400",
            },
            "reconstruction_capacity": {
                "capacity_basis": "terrain_upper_bound",
                "primary_resource_kind": "shape",
                "by_resource": {
                    "shape": {
                        "max_throughput_per_min": "3840.0000",
                        "output_unit": "shapes_per_min",
                        "capacity_upper_bound_platform_count": 8,
                        "source_kind": "CANON_MANUAL",
                    },
                    "fluid": {
                        "max_throughput_per_min": "0.0000",
                        "output_unit": "L_per_min",
                        "capacity_upper_bound_platform_count": 0,
                        "source_kind": "CANON_MANUAL",
                    },
                },
            },
        },
    )
    assert row["capacity"]["shape_max_throughput_per_min"] == "3840.0000"
    assert row["capacity"]["fluid_max_throughput_per_min"] == "0.0000"
    assert row["capacity"]["platform_upper_bound"] == 8
    assert row["capacity"]["primary_resource_kind"] == "shape"
    assert row["capacity"]["fluid_platform_count"] == 0
    assert row["reconstruction"]["display_cell_count"] == 120
    assert row["reconstruction"]["shape_confirmed_cell_count"] == 8
    assert row["reconstruction"]["fluid_confirmed_cell_count"] == 0
    assert row["reconstruction"]["confirmed_cell_count"] == 8
    assert row["reconstruction"]["quality_tier_short"] == "HIGH"
    assert row["rttp"]["confirmed_count"] == 1
    assert row["rttp"]["actual_output_status"] == "pending_pr_2b"


def test_lab_run_summary_legacy_missing_capacity_sections() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=1,
        status="failed",
        solver_summary={"validation_passed": False, "confirmed_count": 0},
    )
    assert row["capacity"]["shape_max_throughput_per_min"] == "—"
    assert row["reconstruction"]["cell_count"] == "—"
    assert row["rttp"]["confirmed_count"] == 0


def test_lab_run_summary_placed_and_first_issue_detail() -> None:
    detail = {
        "issue_code": "extractor_not_connected",
        "coord": [0, 0],
        "candidate_id": "a:1",
        "route_reservation_id": "a:1:route:0",
        "transport_kind": None,
        "message": "output stub not on reservation path",
    }
    row = lab_run_summary_from_solver_summary(
        run_id=21,
        status="failed",
        solver_summary={
            "validation_passed": False,
            "confirmed_count": 14,
            "issue_codes": ["extractor_not_connected"],
            "issue_details": [detail],
        },
    )
    assert row["placed"] == 14
    assert row["miners"] == 14
    assert "connected" not in row
    assert row["first_issue_detail"] == detail


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


def test_lab_run_summary_from_orm_partial_status() -> None:
    proj = m.AsteroidProject.objects.create(name="Partial", slug="runs-partial")
    partial = m.SolverRun.objects.create(
        project=proj,
        run_key="partial",
        algorithm_label="runtime_v0",
        status=m.SolverRun.RunStatus.PARTIAL,
        config_json={
            SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {
                "validation_passed": True,
                "capacity_satisfied": False,
                "run_success": False,
                "placement_capacity_satisfied": False,
                "throughput_budget_satisfied": True,
                "confirmed_count": 6,
                "confirmed_throughput": 96,
                "target_miner_bundle_count": 84,
                "target_placement_count": 84,
                "capacity_deficit_count": 78,
                "throughput_deficit_count": 0,
                "issue_codes": ["under_target_throughput"],
            }
        },
    )
    row = lab_run_summary_from_orm(partial)
    assert row["status"] == "partial"
    assert row["capacity_satisfied"] is False
    assert row["placement_capacity_satisfied"] is False
    assert row["throughput_budget_satisfied"] is True
    assert row["placed"] == 6
    assert row["capacity_deficit_count"] == 78
    assert row["throughput_deficit_count"] == 0
