"""Track B — ``scan_rttp_slug_certification`` management command (mocked runtime)."""

from __future__ import annotations

import base64
import gzip
import json
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.contracts import rttp_ops_policy as policy
from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    CERT_STATUS_CERTIFIED_PASS,
    CERT_STATUS_FAIL_RUNTIME,
    CERT_STATUS_SKIPPED_DIAGNOSTIC,
    RTTP_DIAGNOSTIC_CANON_SLUG,
    RTTP_PASS_CAPABLE_SLUGS,
    evaluate_t3_certification,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.rttp_slug_certification_scan import (
    SCAN_SCHEMA_VERSION,
    resolve_scan_projects,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    SolverRuntimeEntryResult,
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


def _certified_summary() -> dict[str, object]:
    return {
        "validation_passed": True,
        "issue_codes": [],
        "confirmed_count": 2,
        "throughput_budget_satisfied": True,
        "actual_committed_output_per_min": "7680.0000",
        "target_throughput_per_min": "7536.0000",
        "algorithm_steps": [
            {
                "step_id": RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value,
                "passed": True,
            },
            {
                "step_id": RttpAlgorithmStepId.RTTP_COMMIT.value,
                "passed": True,
                "metrics": {"validation_passed": True, "committed_ids": ["c1"]},
            },
        ],
    }


def _mock_runtime_result(
    *,
    summary: dict[str, object],
    solver_run_id: int = 201,
    ok: bool = True,
) -> SolverRuntimeEntryResult:
    return SolverRuntimeEntryResult(
        ok=ok,
        solver_run_id=solver_run_id,
        lab_replay_frames_json=[],
        replay_track_metrics={},
        solver_summary=dict(summary),
        validation_passed=bool(summary.get("validation_passed")),
    )


@patch(
    "django_apps.asteroid_lab.services.rttp_slug_certification_scan.run_solver_runtime_for_project"
)
def test_scan_command_emits_json_result_for_unknown_slug(mock_run) -> None:
    proj = m.AsteroidProject.objects.create(name="ScanJson", slug="scan-json-slug")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    mock_run.return_value = _mock_runtime_result(summary=_certified_summary())

    out = StringIO()
    call_command(
        "scan_rttp_slug_certification",
        slug=proj.slug,
        json=True,
        stdout=out,
    )
    report = json.loads(out.getvalue())
    assert report["schema_version"] == SCAN_SCHEMA_VERSION
    assert report["candidate_count"] == 1
    assert report["certified_pass_count"] == 1
    row = report["results"][0]
    assert row["slug"] == proj.slug
    assert row["slug_class"] == "unknown"
    assert row["cert_status"] == CERT_STATUS_CERTIFIED_PASS
    assert row["solver_run_id"] == 201
    assert row["t0_passed"] is True
    assert row["t1b_passed"] is True
    assert row["t2_passed"] is True
    assert row["t3_shell_passed"] is True
    assert row["issue_codes"] == []
    assert row["actual_committed"] == 7680
    assert row["throughput_target_min"] == 7536
    mock_run.assert_called_once()


def test_resolve_scan_projects_excludes_diagnostic_canon_by_default() -> None:
    diag = m.AsteroidProject.objects.create(
        name="Diag",
        slug=RTTP_DIAGNOSTIC_CANON_SLUG,
    )
    create_copy_code_map_input(diag, _minimal_valid_copy())
    other = m.AsteroidProject.objects.create(name="Other", slug="scan-other-slug")
    create_copy_code_map_input(other, _minimal_valid_copy())

    slugs = {p.slug for p in resolve_scan_projects(include_diagnostic=False)}
    assert RTTP_DIAGNOSTIC_CANON_SLUG not in slugs
    assert "scan-other-slug" in slugs


@patch(
    "django_apps.asteroid_lab.services.rttp_slug_certification_scan.run_solver_runtime_for_project"
)
def test_scan_command_skips_diagnostic_canon_by_default(mock_run) -> None:
    m.AsteroidProject.objects.create(name="Diag", slug=RTTP_DIAGNOSTIC_CANON_SLUG)
    other = m.AsteroidProject.objects.create(name="Other", slug="scan-other-only")
    create_copy_code_map_input(other, _minimal_valid_copy())
    mock_run.return_value = _mock_runtime_result(
        summary={
            "validation_passed": False,
            "issue_codes": ["throughput_target_shortfall"],
            "confirmed_count": 1,
            "throughput_budget_satisfied": False,
            "algorithm_steps": _certified_summary()["algorithm_steps"],
        }
    )

    call_command(
        "scan_rttp_slug_certification",
        slug="scan-other-only",
        json=True,
        stdout=StringIO(),
    )
    mock_run.assert_called_once()


@patch(
    "django_apps.asteroid_lab.services.rttp_slug_certification_scan.run_solver_runtime_for_project"
)
def test_scan_command_can_include_diagnostic_canon(mock_run) -> None:
    diag = m.AsteroidProject.objects.create(
        name="DiagIncl",
        slug=RTTP_DIAGNOSTIC_CANON_SLUG,
    )
    create_copy_code_map_input(diag, _minimal_valid_copy())

    out = StringIO()
    call_command(
        "scan_rttp_slug_certification",
        slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        include_diagnostic=True,
        json=True,
        stdout=out,
    )
    report = json.loads(out.getvalue())
    assert len(report["results"]) == 1
    assert report["results"][0]["cert_status"] == CERT_STATUS_SKIPPED_DIAGNOSTIC
    mock_run.assert_not_called()


@patch(
    "django_apps.asteroid_lab.services.rttp_slug_certification_scan.evaluate_t3_certification",
    wraps=evaluate_t3_certification,
)
@patch(
    "django_apps.asteroid_lab.services.rttp_slug_certification_scan.run_solver_runtime_for_project"
)
def test_scan_command_uses_evaluate_t3_certification(mock_run, mock_eval) -> None:
    proj = m.AsteroidProject.objects.create(name="EvalSpy", slug="scan-eval-spy")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    summary = _certified_summary()
    mock_run.return_value = _mock_runtime_result(summary=summary)

    call_command(
        "scan_rttp_slug_certification",
        slug=proj.slug,
        json=True,
        stdout=StringIO(),
    )
    mock_eval.assert_called_once()
    _args, kwargs = mock_eval.call_args
    assert kwargs["slug"] == proj.slug
    assert kwargs["solver_summary"]["validation_passed"] is True
    assert len(kwargs["pipeline_steps"]) == 2


@patch(
    "django_apps.asteroid_lab.services.rttp_slug_certification_scan.run_solver_runtime_for_project"
)
def test_scan_command_does_not_mutate_pass_capable_registry(mock_run) -> None:
    before = frozenset(RTTP_PASS_CAPABLE_SLUGS)
    proj = m.AsteroidProject.objects.create(name="NoMut", slug="scan-no-mutate")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    mock_run.return_value = _mock_runtime_result(summary=_certified_summary())

    call_command(
        "scan_rttp_slug_certification",
        slug=proj.slug,
        json=True,
        stdout=StringIO(),
    )
    assert policy.RTTP_PASS_CAPABLE_SLUGS == before


@patch(
    "django_apps.asteroid_lab.services.rttp_slug_certification_scan.run_solver_runtime_for_project"
)
def test_scan_command_maps_runtime_failure_to_fail_runtime(mock_run) -> None:
    proj = m.AsteroidProject.objects.create(name="FailRt", slug="scan-fail-runtime")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    mock_run.return_value = SolverRuntimeEntryResult(
        ok=False,
        solver_run_id=None,
        lab_replay_frames_json=[],
        replay_track_metrics={},
        solver_summary={},
        validation_passed=False,
        error_code=SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE,
        message="RTTP disabled",
    )

    out = StringIO()
    call_command(
        "scan_rttp_slug_certification",
        slug=proj.slug,
        json=True,
        stdout=out,
    )
    row = json.loads(out.getvalue())["results"][0]
    assert row["cert_status"] == CERT_STATUS_FAIL_RUNTIME
    assert row["runtime_error_code"] == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value
