"""SolverRun.config_json exterior connector plan wire helper."""

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    _exterior_connector_plan_wire_for_run,
)


@pytest.fixture
def solver_run_project() -> m.AsteroidProject:
    return m.AsteroidProject.objects.create(name="L2 wire", slug="l2-wire-proj")


@pytest.mark.django_db
def test_exterior_connector_plan_wire_reads_config_json_top_level(
    solver_run_project: m.AsteroidProject,
) -> None:
    run = m.SolverRun.objects.create(
        project=solver_run_project,
        run_key="rk-l2-1",
        config_json={"exterior_connector_plan": {"version": "exterior_connector_plan.v1"}},
    )
    wire = _exterior_connector_plan_wire_for_run(run)
    assert wire is not None
    assert wire.get("version") == "exterior_connector_plan.v1"


@pytest.mark.django_db
def test_exterior_connector_plan_wire_reads_nested_solver_summary(
    solver_run_project: m.AsteroidProject,
) -> None:
    run = m.SolverRun.objects.create(
        project=solver_run_project,
        run_key="rk-l2-2",
        config_json={
            "solver_summary": {"exterior_connector_plan": {"planned_connectors": []}},
        },
    )
    wire = _exterior_connector_plan_wire_for_run(run)
    assert isinstance(wire, dict)


def test_exterior_connector_plan_wire_none_when_run_missing() -> None:
    assert _exterior_connector_plan_wire_for_run(None) is None
