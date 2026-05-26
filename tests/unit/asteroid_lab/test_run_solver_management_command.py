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
from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
)
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import SolverRuntimeEntryResult

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


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_deferred_retry_execute_sets_config() -> None:
    proj = m.AsteroidProject.objects.create(name="CliDefer", slug="cli-run-defer-exec")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit) as exc_info:
        call_command(
            "run_solver",
            slug=proj.slug,
            deferred_retry_execute=True,
            no_replay=True,
            stdout=out,
            stderr=StringIO(),
        )
    assert exc_info.value.code == 1
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert run is not None
    shadow = (run.config_json or {}).get(SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY)
    assert shadow == {"enabled": True, "observe_only": False}
    assert run.config_json.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY) is not True


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_deferred_retry_execute_json_stdout() -> None:
    proj = m.AsteroidProject.objects.create(name="CliDeferJson", slug="cli-run-defer-json")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit) as exc_info:
        call_command(
            "run_solver",
            slug=proj.slug,
            deferred_retry_execute=True,
            no_replay=True,
            json=True,
            stdout=out,
            stderr=StringIO(),
        )
    assert exc_info.value.code == 1
    body = json.loads(out.getvalue())
    assert body.get("solver_run_id") is not None
    assert "solver_summary" in body


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_selection_mode_evolution_sets_config() -> None:
    proj = m.AsteroidProject.objects.create(name="CliGa2", slug="cli-run-ga2-evolution")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit) as exc_info:
        call_command(
            "run_solver",
            slug=proj.slug,
            selection_mode="evolution",
            no_replay=True,
            stdout=out,
            stderr=StringIO(),
        )
    assert exc_info.value.code == 1
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert run is not None
    selection = (run.config_json or {}).get(SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY) or {}
    assert selection.get("mode") == "evolution"
    ga_shadow = (run.config_json or {}).get(SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY) or {}
    assert ga_shadow.get("enabled") is True


def test_run_solver_macro_only_and_selection_mode_evolution_raises() -> None:
    proj = m.AsteroidProject.objects.create(name="CliGa2Conflict", slug="cli-ga2-macro-conflict")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    with pytest.raises(CommandError, match="Cannot combine"):
        call_command(
            "run_solver",
            slug=proj.slug,
            macro_only=True,
            selection_mode="evolution",
            stderr=StringIO(),
        )


def test_run_solver_macro_only_and_deferred_retry_raises() -> None:
    proj = m.AsteroidProject.objects.create(name="CliConflict", slug="cli-run-defer-conflict")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    with pytest.raises(CommandError, match="Cannot combine"):
        call_command(
            "run_solver",
            slug=proj.slug,
            macro_only=True,
            deferred_retry_execute=True,
            stderr=StringIO(),
        )


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_prints_t2_policy_line_for_diagnostic_shortfall(monkeypatch) -> None:
    proj = m.AsteroidProject.objects.create(name="CliT2Policy", slug="cli-t2-policy-line")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    summary = {
        "validation_passed": True,
        "diagnostic_expected_shortfall": True,
        "t2_policy_status": T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
        "issue_codes": ["throughput_target_shortfall"],
    }
    fake_result = SolverRuntimeEntryResult(
        ok=True,
        solver_run_id=999,
        lab_replay_frames_json=[],
        replay_track_metrics={},
        solver_summary=summary,
        validation_passed=True,
    )
    monkeypatch.setattr(
        "django_apps.asteroid_lab.management.commands.run_solver.run_solver_runtime_for_project",
        lambda *_args, **_kwargs: fake_result,
    )
    out = StringIO()
    call_command("run_solver", slug=proj.slug, stdout=out, stderr=StringIO(), no_replay=True)
    assert "t2_policy: expected_diagnostic_shortfall" in out.getvalue()


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_prints_pass_capable_slug_class_line(monkeypatch) -> None:
    proj = m.AsteroidProject.objects.create(name="CliPassCap", slug="cli-pass-capable-line")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    summary = {
        "validation_passed": True,
        "rttp_ops_slug_class": "pass_capable",
        "throughput_budget_satisfied": True,
        "issue_codes": [],
    }
    fake_result = SolverRuntimeEntryResult(
        ok=True,
        solver_run_id=1000,
        lab_replay_frames_json=[],
        replay_track_metrics={},
        solver_summary=summary,
        validation_passed=True,
    )
    monkeypatch.setattr(
        "django_apps.asteroid_lab.management.commands.run_solver.run_solver_runtime_for_project",
        lambda *_args, **_kwargs: fake_result,
    )
    out = StringIO()
    call_command("run_solver", slug=proj.slug, stdout=out, stderr=StringIO(), no_replay=True)
    text = out.getvalue()
    assert "rttp_ops_slug_class: pass_capable (T3 reference slug)" in text
    assert "expected_diagnostic_shortfall" not in text


def test_run_solver_command_unknown_slug_raises() -> None:
    with pytest.raises(CommandError, match="Unknown project slug"):
        call_command("run_solver", slug="no-such-project-slug")


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_run_solver_command_solver_not_available_raises() -> None:
    proj = m.AsteroidProject.objects.create(name="CliStub", slug="cli-run-stub")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    with pytest.raises(CommandError, match="SOLVER_NOT_AVAILABLE"):
        call_command("run_solver", slug=proj.slug, stderr=StringIO())
