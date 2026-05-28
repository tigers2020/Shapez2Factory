"""CLI ``manage.py run_solver`` — stub path (SOLVER_NOT_AVAILABLE)."""

from __future__ import annotations

import base64
import gzip
import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input

pytestmark = pytest.mark.django_db


def _minimal_valid_copy() -> str:
    payload = json.dumps(
        {
            "V": 1,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(payload)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_run_solver_command_solver_not_available_raises() -> None:
    proj = m.AsteroidProject.objects.create(name="CliStub", slug="cli-run-stub")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    with pytest.raises(CommandError, match="SOLVER_NOT_AVAILABLE"):
        call_command("run_solver", slug=proj.slug, stderr=StringIO())


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_command_solver_not_available_raises_when_rttp_flag_true() -> None:
    proj = m.AsteroidProject.objects.create(name="CliStubOn", slug="cli-run-stub-on")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    with pytest.raises(CommandError, match="SOLVER_NOT_AVAILABLE"):
        call_command("run_solver", slug=proj.slug, stderr=StringIO())


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_run_solver_command_json_stdout_includes_error_code() -> None:
    proj = m.AsteroidProject.objects.create(name="CliJson", slug="cli-run-json")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(CommandError, match="SOLVER_NOT_AVAILABLE"):
        call_command("run_solver", slug=proj.slug, json=True, stdout=out, stderr=StringIO())
    body = json.loads(out.getvalue())
    assert body.get("ok") is False
    assert body.get("error_code") == "SOLVER_NOT_AVAILABLE"


def test_run_solver_command_unknown_slug_raises() -> None:
    with pytest.raises(CommandError, match="Unknown project slug"):
        call_command("run_solver", slug="no-such-project-slug")
