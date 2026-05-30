"""CLI ``manage.py run_solver`` when Layer 02 solver is disabled."""

from __future__ import annotations

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from django_apps.asteroid_lab import models as m
pytestmark = pytest.mark.django_db


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=False)
def test_run_solver_command_solver_not_available_raises() -> None:
    proj = m.AsteroidProject.objects.create(name="CliStub", slug="cli-run-stub")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    with pytest.raises(CommandError, match="SOLVER_NOT_AVAILABLE"):
        call_command("run_solver", slug=proj.slug, stderr=StringIO())


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=False)
def test_run_solver_command_json_stdout_includes_error_code() -> None:
    proj = m.AsteroidProject.objects.create(name="CliJson", slug="cli-run-json")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    out = StringIO()
    with pytest.raises(CommandError, match="SOLVER_NOT_AVAILABLE"):
        call_command("run_solver", slug=proj.slug, json=True, stdout=out, stderr=StringIO())
    payload = json.loads(out.getvalue())
    assert payload["error_code"] == "SOLVER_NOT_AVAILABLE"
