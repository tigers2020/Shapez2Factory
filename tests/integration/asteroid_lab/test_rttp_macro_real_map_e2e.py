"""Real-map macro E2E: committed copy → reconstruction → macro_only runtime (no monkeypatch)."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)

pytestmark = [pytest.mark.django_db, pytest.mark.integration]

_FIXTURE_COPY = (
    Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "macro_e2e_copy.code"
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def _macro_e2e_copy_code() -> str:
    raw = _FIXTURE_COPY.read_text(encoding="utf-8").strip()
    if not raw.startswith("SHAPEZ2-"):
        msg = f"invalid macro E2E copy fixture: {_FIXTURE_COPY}"
        raise AssertionError(msg)
    return raw


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_macro_only_on_real_map_copy_fixture() -> None:
    """OPS-verified map (copy-import class) through full runtime without input monkeypatch."""

    proj = m.AsteroidProject.objects.create(
        name="MacroRealMapE2E",
        slug="macro-real-map-e2e",
    )
    create_copy_code_map_input(proj, _macro_e2e_copy_code())

    result = run_solver_runtime_for_project(
        int(proj.pk),
        run_key="macro-real-map-e2e",
        config={
            SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: True,
            SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY: False,
        },
    )

    assert result.solver_run_id is not None
    assert result.validation_passed is True
    assert result.ok is True

    summary = dict(result.solver_summary)
    assert summary.get("macro_only_mode") is True
    hud = summary.get("macro_commit_summary")
    assert isinstance(hud, dict)
    assert hud.get("macro_only_mode") is True
    assert hud.get("validation_passed") is True
    assert hud.get("conflict_count") == 0
    assert len(hud.get("committed_macro_ids") or []) == 1
    assert len(hud.get("committed_child_ids") or []) == 3
    assert hud.get("domain_version") is not None

    body = entry_result_to_json_dict(result)
    run_summary = body.get("run_summary")
    assert isinstance(run_summary, dict)
    assert run_summary.get("macro_commit_summary") == hud

    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    assert run.config_json.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY) is True
    persisted = (run.config_json or {}).get(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY) or {}
    assert persisted.get("macro_commit_summary") == hud
