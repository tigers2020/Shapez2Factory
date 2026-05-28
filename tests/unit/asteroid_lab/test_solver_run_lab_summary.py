"""Lab UI solver run summary serialization (read-only)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
    overlay_field_cell_count,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
    build_reconstruction_observability,
)
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
    assert row["throughput_budget_satisfied"] is None
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
                        "max_throughput_per_min": "960.0000",
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
    assert row["capacity"]["shape_max_throughput_per_min"] == "960.0000"
    assert row["capacity"]["fluid_max_throughput_per_min"] == "0.0000"
    assert row["capacity"]["platform_upper_bound"] == 8
    assert row["capacity"]["primary_resource_kind"] == "shape"
    assert row["capacity"]["fluid_platform_count"] == 0
    assert row["reconstruction"]["display_cell_count"] == 120
    assert row["reconstruction"]["asteroid_field_cell_count"] == 8
    assert row["reconstruction"]["shape_field_cell_count"] == 8
    assert row["reconstruction"]["fluid_field_cell_count"] == 0
    assert row["reconstruction"]["quality_tier_short"] == "HIGH"
    assert row["rttp"]["confirmed_count"] == 1
    assert row["rttp"]["actual_output_status"] == "pending_pr_2b"


def test_lab_run_summary_throughput_target_section() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=77,
        status="completed",
        solver_summary={
            "validation_passed": True,
            "confirmed_count": 2,
            "actual_committed_output_per_min": "2400.0000",
            "throughput_target_percent": 60,
            "target_throughput_per_min": "2880.0000",
            "reconstruction_max_throughput_per_min": "4800.0000",
            "throughput_budget_satisfied": False,
            "throughput_shortfall_per_min": "480.0000",
            "target_utilization_ratio": "0.6000",
            "actual_utilization_ratio": "0.5000",
            "throughput_target_status": "shortfall",
        },
    )
    assert row["throughput_target"]["budget_status"] == "shortfall"
    assert row["throughput_target"]["throughput_target_percent"] == 60
    assert row["throughput_budget_satisfied"] is False


def test_lab_run_summary_throughput_budget_unknown_without_actual() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=78,
        status="failed",
        solver_summary={
            "validation_passed": False,
            "throughput_budget_satisfied": False,
            "throughput_target_percent": 80,
        },
    )
    assert row["throughput_budget_satisfied"] is None
    assert row["throughput_target"]["budget_status"] == "—"


def test_lab_run_summary_actual_output_status_available() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=42,
        status="completed",
        solver_summary={
            "validation_passed": True,
            "confirmed_count": 2,
            "actual_committed_output_per_min": "480.0000",
        },
    )
    assert row["rttp"]["actual_output_status"] == "available"
    assert row["rttp"]["actual_committed_output_per_min"] == "480.0000"


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


def test_lab_run_summary_from_solver_summary_exposes_meg_fields() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=42,
        status="partial",
        solver_summary={
            "validation_passed": False,
            "run_status": "partial_success",
            "structural_validation_passed": True,
            "optimization_goal": {
                "passed": False,
                "issue_code": "mining_equipment_goal_shortfall",
                "target_mining_equipment_cells": 467,
                "confirmed_passed_mining_equipment_cells": 25,
                "shortfall": 442,
                "confirmed_committed_bundle_count": 25,
            },
            "issue_codes": ["mining_equipment_goal_shortfall"],
            "confirmed_count": 25,
        },
    )
    assert row["run_status"] == "partial_success"
    assert row["structural_validation_passed"] is True
    assert row["optimization_goal"]["shortfall"] == 442
    assert row["validation_passed"] is False


def test_lab_run_summary_from_orm_partial_status() -> None:
    proj = m.AsteroidProject.objects.create(name="Partial", slug="runs-partial")
    partial = m.SolverRun.objects.create(
        project=proj,
        run_key="partial",
        algorithm_label="runtime_v0",
        status=m.SolverRun.RunStatus.PARTIAL,
        config_json={
            SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {
                "validation_passed": False,
                "run_status": "partial_success",
                "structural_validation_passed": True,
                "optimization_goal": {
                    "passed": False,
                    "issue_code": "mining_equipment_goal_shortfall",
                    "shortfall": 10,
                },
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
                "issue_codes": ["mining_equipment_goal_shortfall"],
            }
        },
    )
    row = lab_run_summary_from_orm(partial)
    assert row["status"] == "partial"
    assert row["run_status"] == "partial_success"
    assert row["optimization_goal"]["issue_code"] == "mining_equipment_goal_shortfall"
    assert row["capacity_satisfied"] is False
    assert row["placement_capacity_satisfied"] is False
    assert row["throughput_budget_satisfied"] is None
    assert row["placed"] == 6
    assert row["capacity_deficit_count"] == 78
    assert row["throughput_deficit_count"] == 0


def test_lab_capacity_uses_complete_map_even_when_overlay_is_sparse() -> None:
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)

    obs = build_reconstruction_observability(recon=recon, complete_map=complete)
    cap = build_reconstruction_capacity_envelope(complete_map=complete)

    overlay_cells = len(recon.cells)
    display_cells = len(complete.cells)
    overlay_fields = overlay_field_cell_count(recon)
    complete_fields = len(complete.field_cells)
    shape_platform = cap["by_resource"]["shape"]["capacity_upper_bound_platform_count"]

    assert overlay_cells != display_cells
    assert overlay_fields < complete_fields
    assert shape_platform == complete.shape_field_cell_count
    assert shape_platform != overlay_fields

    row = lab_run_summary_from_solver_summary(
        run_id=1,
        status="completed",
        solver_summary={
            "validation_passed": True,
            "confirmed_count": 0,
            "reconstruction_observability": obs,
            "reconstruction_capacity": cap,
        },
    )
    assert row["capacity"]["platform_upper_bound"] == shape_platform
    assert row["reconstruction"]["asteroid_field_cell_count"] == complete_fields
    assert row["reconstruction"]["shape_field_cell_count"] == complete.shape_field_cell_count
