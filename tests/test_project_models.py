import pytest

from django_apps.projects.models import SolverProject, SolverRun, SolverRunStatus


@pytest.mark.django_db
def test_solver_run_defaults_capture_reproducible_state() -> None:
    project = SolverProject.objects.create(
        title="Starter",
        target_shape="CuRuSuWu",
        target_rate_per_min=120.0,
        solver_settings={"max_depth": 12},
    )

    run = SolverRun.objects.create(
        project=project,
        input_snapshot={
            "target_shape": "CuRuSuWu",
            "target_rate_per_min": 120,
            "available_inputs": ["CuCuCuCu"],
            "enabled_operations": ["cut", "rotate", "stack"],
            "max_depth": 12,
            "game_version": "shapez2_1_0",
        },
    )

    assert run.status == SolverRunStatus.QUEUED
    assert run.input_snapshot["game_version"] == "shapez2_1_0"
    assert project.runs.count() == 1
