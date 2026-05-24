"""CLI ``manage.py run_solver`` — same runtime path as HTTP run-solver."""

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
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


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


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_command_prints_summary_for_slug() -> None:
    proj = m.AsteroidProject.objects.create(name="CliRun", slug="cli-run-solver")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit) as exc_info:
        call_command("run_solver", slug=proj.slug, stdout=out, stderr=StringIO(), no_replay=True)
    assert exc_info.value.code == 1
    text = out.getvalue()
    assert "solver_run_id:" in text
    assert "validation_passed:" in text
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert run is not None
    assert run.config_json.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY) is not True


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_command_macro_only_sets_config() -> None:
    proj = m.AsteroidProject.objects.create(name="CliMacro", slug="cli-run-macro")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit) as exc_info:
        call_command(
            "run_solver",
            slug=proj.slug,
            macro_only=True,
            no_replay=True,
            stdout=out,
            stderr=StringIO(),
        )
    assert exc_info.value.code == 1
    assert "macro_only_mode: True" in out.getvalue()
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert run is not None
    assert run.config_json.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY) is True
    assert (run.config_json or {}).get("solver_summary")


def test_run_solver_command_unknown_slug_raises() -> None:
    with pytest.raises(CommandError, match="Unknown project slug"):
        call_command("run_solver", slug="no-such-project-slug")


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_run_solver_command_solver_not_available_raises() -> None:
    proj = m.AsteroidProject.objects.create(name="CliStub", slug="cli-run-stub")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    with pytest.raises(CommandError, match="SOLVER_NOT_AVAILABLE"):
        call_command("run_solver", slug=proj.slug, stderr=StringIO())
