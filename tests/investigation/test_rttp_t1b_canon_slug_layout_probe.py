"""E-track: diagnostic canon slug layout assert probe (read-only)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    validate_pipeline_layout,
)
from harness.investigation.rttp_final_layout_assert_probe import (
    FinalLayoutAssertCode,
    diagnose_final_layout,
)
from harness.investigation.rttp_t1b_step_forensics import extract_t1b_forensics
from tests.unit.asteroid_lab._runtime_game_data import run_solver_runtime_with_pinned_game_data

CANON_SLUG = "copy-import-495e552c"

pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.slow]


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.fixture
def canon_project_id() -> int:
    project = m.AsteroidProject.objects.filter(slug=CANON_SLUG).first()
    if project is None:
        pytest.skip(f"Canon slug {CANON_SLUG!r} not in DB — import map first")
    return int(project.id)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_canon_slug_t1b_layout_assert_probe(canon_project_id: int) -> None:
    captured: dict[str, object] = {}

    def _capture_validate_pipeline_layout(**kwargs: object) -> tuple[bool, object | None]:
        captured.update(kwargs)
        return validate_pipeline_layout(**kwargs)  # type: ignore[arg-type]

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.validate_pipeline_layout",
        side_effect=_capture_validate_pipeline_layout,
    ):
        result = run_solver_runtime_with_pinned_game_data(
            canon_project_id,
            config={"throughput_target_percent": 10},
        )

    assert captured, "validate_pipeline_layout was not invoked"
    committed_ids = captured["committed_ids"]
    reserved_route_cells = captured["reserved_route_cells"]
    candidates_by_id = captured["candidates_by_id"]
    inp = captured["inp"]

    code, detail = diagnose_final_layout(
        committed_ids,  # type: ignore[arg-type]
        reserved_route_cells,  # type: ignore[arg-type]
        candidates_by_id,  # type: ignore[arg-type]
        inp,  # type: ignore[arg-type]
    )

    steps = result.solver_summary.get("algorithm_steps") or []
    forensics = extract_t1b_forensics(steps)

    assert forensics["committed_count"] > 0
    assert forensics["catalog_passed"] is True
    assert forensics["validation_passed"] is False
    assert forensics["pipeline_composition_anomaly"] is False
    assert code is not FinalLayoutAssertCode.FL_OK, detail

    # Persist primary FL-xx for investigation report (pytest -s visibility).
    print(f"T1B_PRIMARY_FL_XX={code.value}")
    print(f"T1B_PRIMARY_FL_DETAIL={detail}")
    print(f"T1B_FORENSICS={forensics}")
    print(f"T1B_SOLVER_RUN_ID={result.solver_run_id}")
