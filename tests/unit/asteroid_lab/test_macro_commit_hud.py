"""HUD macro commit summary — output-only observability (never solver input)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RttpAlgorithmStepId,
    extract_macro_commit_summary,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_solver_summary,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    _rttp_pipeline_config_from_run_config,
)

pytestmark = pytest.mark.django_db

_COMMIT_STEP = {
    "step_id": RttpAlgorithmStepId.RTTP_COMMIT.value,
    "metrics": {
        "committed_macro_ids": ["m1"],
        "committed_child_ids": ["c1", "c2", "c3"],
        "domain_version": 3,
        "conflict_count": 0,
    },
}


def test_macro_commit_summary_visible_when_macro_only() -> None:
    hud = extract_macro_commit_summary(
        (_COMMIT_STEP,),
        macro_only_mode=True,
        validation_passed=True,
    )
    assert hud is not None
    assert hud["macro_only_mode"] is True
    assert hud["committed_macro_ids"] == ["m1"]
    assert hud["committed_child_ids"] == ["c1", "c2", "c3"]
    assert hud["domain_version"] == 3
    assert hud["validation_passed"] is True
    assert hud["conflict_count"] == 0

    row = lab_run_summary_from_solver_summary(
        run_id=1,
        status="completed",
        solver_summary={
            "validation_passed": True,
            "macro_only_mode": True,
            "macro_commit_summary": hud,
        },
    )
    assert row["macro_commit_summary"] == hud


def test_macro_commit_summary_absent_for_normal_run() -> None:
    assert (
        extract_macro_commit_summary(
            (_COMMIT_STEP,),
            macro_only_mode=False,
            validation_passed=True,
        )
        is None
    )
    row = lab_run_summary_from_solver_summary(
        run_id=2,
        status="completed",
        solver_summary={"validation_passed": True, "macro_only_mode": False},
    )
    assert "macro_commit_summary" not in row


def test_macro_commit_summary_does_not_drive_solver_config() -> None:
    config = {
        SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {
            "macro_commit_summary": {
                "committed_macro_ids": ["must-not-read"],
                "domain_version": 99,
            }
        },
        SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: False,
        SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY: True,
        SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY: 8,
    }
    pipeline_cfg = _rttp_pipeline_config_from_run_config(config)
    assert pipeline_cfg.macro_only_mode is False
    assert pipeline_cfg.max_macro_candidates == 8
    allowed = {
        SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
        SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
        SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
        "rttp_enabled",
        SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    }
    for key in config:
        if key not in allowed:
            continue
        if key == SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY:
            assert "macro_commit_summary" in config[key]
