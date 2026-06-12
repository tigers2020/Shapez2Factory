"""Layer 02 solver runtime entry (Run Solver button)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services import solver_runtime_entry
from django_apps.asteroid_lab.services.artifact_ingest import ArtifactIngestResult
from django_apps.asteroid_lab.services.artifact_manifest_reader import ArtifactManifestRecord
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)
from django_apps.asteroid_lab.services.solver_runtime_types import SolverRuntimeEntryResult
from django_apps.asteroid_lab.services.solver_subprocess_runner import SolverSubprocessResult
from django_apps.asteroid_lab.services.subprocess_stream_tee import SubprocessTeeResult

pytestmark = pytest.mark.django_db

_REPO = Path(__file__).resolve().parents[3]
_COPY_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "reconstruction_required_.txt"
_SNAPSHOT_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "game_data_snapshot_min.json"


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


def _minimal_snapshot_payload() -> dict[str, object]:
    return {"schema_version": "game_data_snapshot_v1"}


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_entry_result_json_includes_run_summary_for_subprocess_run() -> None:
    proj = m.AsteroidProject.objects.create(name="SubprocessJson", slug="subprocess-json")
    run = m.SolverRun.objects.create(
        project=proj,
        run_key="subprocess-json-run",
        status=m.SolverRun.RunStatus.COMPLETED,
        solver_summary_json={"validation_passed": True},
    )
    result = SolverRuntimeEntryResult(
        ok=True,
        solver_run_id=int(run.pk),
        lab_replay_frames_json=[],
        replay_track_metrics={"frame_count": 0},
        solver_summary={"validation_passed": True},
        validation_passed=True,
    )
    body = entry_result_to_json_dict(result, project_slug=str(proj.slug))
    run_summary = body.get("run_summary")
    assert isinstance(run_summary, dict)
    assert str(run_summary["id"]) == str(result.solver_run_id)


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
@override_settings(
    ASTEROID_LAB_SOLVER_MODE="subprocess_only",
    ASTEROID_LAB_ARTIFACT_ROOT="F:/tmp/asteroid-test-runs",
    ASTEROID_LAB_SUBPROCESS_TIMEOUT_SECONDS=7,
)
def test_run_solver_invokes_cli_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    proj = m.AsteroidProject.objects.create(name="Subprocess", slug="subprocess")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    calls: list[dict[str, object]] = []

    def fake_run_solver_subprocess(
        request: object,
        **kwargs: object,
    ) -> SolverSubprocessResult:
        calls.append({"request": request, **kwargs})
        return SolverSubprocessResult(
            run_key=request.run_key,
            artifact_dir=request.artifact_root / request.run_key,
            subprocess_log_path=request.artifact_root / request.run_key / "logs" / "subprocess.log",
            completed=SubprocessTeeResult(
                args=("python", "-m", "shapez2_factory.interfaces.cli.asteroid_solve"),
                returncode=0,
                elapsed_ms=5,
                stdout="",
                stderr="asteroid_cli run end exit=0\n",
            ),
        )

    def fake_ingest_artifact_for_project(**kwargs: object) -> ArtifactIngestResult:
        run = m.SolverRun.objects.create(
            project=proj,
            run_key="django-run-1",
            status=m.SolverRun.RunStatus.COMPLETED,
            solver_summary_json={"validation_passed": True},
        )
        return ArtifactIngestResult(
            solver_run=run,
            manifest=ArtifactManifestRecord(
                schema_version=1,
                run_key="django-run-1",
                lifecycle_status="artifact_written",
                created_at_utc="2026-05-30T00:00:00Z",
                core_build_id="test",
            ),
            solver_summary={"validation_passed": True},
        )

    monkeypatch.setattr(solver_runtime_entry, "run_solver_subprocess", fake_run_solver_subprocess)
    monkeypatch.setattr(
        solver_runtime_entry,
        "ingest_artifact_for_project",
        fake_ingest_artifact_for_project,
    )

    result = run_solver_runtime_for_project(
        int(proj.pk),
        run_key="django-run-1",
        config={"cli_verbose": True},
        game_data_snapshot=_minimal_snapshot_payload(),
    )

    assert result.ok is True
    assert result.error_code is None
    assert result.solver_run_id is not None
    assert result.solver_summary == {"validation_passed": True}
    assert result.validation_passed is True
    assert calls
    request = calls[0]["request"]
    assert request.timeout_seconds == 7
    assert request.verbose is True
    assert calls[0]["tee_to_parent_stderr"] is False


def test_run_solver_subprocess_mode_end_to_end_artifact_ingest(
    tmp_path: Path,
) -> None:
    proj = m.AsteroidProject.objects.create(name="SubprocessE2E", slug="subprocess-e2e")
    copy_text = next(
        line.strip()
        for line in _COPY_FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    m.AsteroidMapInput.objects.create(project=proj, copy_code=copy_text)
    snapshot_payload = json.loads(_SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))

    with override_settings(
        ASTEROID_LAB_ARTIFACT_ROOT=tmp_path,
        ASTEROID_LAB_SUBPROCESS_TIMEOUT_SECONDS=60,
    ):
        result = run_solver_runtime_for_project(
            int(proj.pk),
            run_key="django-e2e",
            config={"solver_mode": "subprocess", "cli_verbose": True},
            game_data_snapshot=snapshot_payload,
        )

    assert result.ok is True
    assert result.error_code is None
    assert result.solver_run_id is not None
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    assert run.run_key == "django-e2e"
    assert run.status == m.SolverRun.RunStatus.COMPLETED
    assert run.solver_runtime_replay_frames_json == []
    assert run.lab_replay_manifest_summary_json["mode"] == "artifact_jsonl"
    artifact_dir = tmp_path / "django-e2e"
    assert (artifact_dir / "manifest.json").is_file()
    assert (artifact_dir / "logs" / "subprocess.log").is_file()
