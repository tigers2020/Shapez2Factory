"""Solver runtime entry must inject a DB-built gene catalog into the subprocess request."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
)
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services import solver_runtime_entry
from django_apps.asteroid_lab.services.artifact_ingest import ArtifactIngestResult
from django_apps.asteroid_lab.services.artifact_manifest_reader import ArtifactManifestRecord
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project
from django_apps.asteroid_lab.services.solver_subprocess_runner import SolverSubprocessResult
from django_apps.asteroid_lab.services.subprocess_stream_tee import SubprocessTeeResult

pytestmark = pytest.mark.django_db


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


def _minimal_snapshot_payload() -> dict[str]:
    return {"schema_version": "game_data_snapshot_v1"}


def _seed_one_sample(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    genes, _ = exhaustive_genes_ext0_belt
    assert genes, "exhaustive generator must produce at least one gene for seeding"
    g = genes[0]
    GeneSeed.objects.update_or_create(
        gene_key=g.key,
        defaults={
            "name": g.name,
            "code": g.encoded_copy_string,
            "metadata_json": dict(g.metadata),
        },
    )


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
@override_settings(
    ASTEROID_LAB_SOLVER_MODE="subprocess_only",
    ASTEROID_LAB_ARTIFACT_ROOT="F:/tmp/asteroid-test-runs",
    ASTEROID_LAB_SUBPROCESS_TIMEOUT_SECONDS=7,
)
def test_run_solver_injects_db_gene_catalog_into_request(
    monkeypatch: pytest.MonkeyPatch,
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    proj = m.AsteroidProject.objects.create(name="GeneCatalog", slug="gene-catalog")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    _seed_one_sample(exhaustive_genes_ext0_belt)

    calls: list[dict[str]] = []

    def fake_run_solver_subprocess(request: object, **kwargs: object) -> SolverSubprocessResult:
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
            run_key="gene-catalog-run",
            status=m.SolverRun.RunStatus.COMPLETED,
            solver_summary_json={"validation_passed": True},
        )
        return ArtifactIngestResult(
            solver_run=run,
            manifest=ArtifactManifestRecord(
                schema_version=1,
                run_key="gene-catalog-run",
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
        run_key="gene-catalog-run",
        config={"cli_verbose": True},
        game_data_snapshot=_minimal_snapshot_payload(),
    )

    assert result.ok is True
    assert calls
    request = calls[0]["request"]
    assert request.genetic_sample_seeds["schema_version"] == "genetic_sample_seed_v1"
    assert len(request.genetic_sample_seeds["entries"]) >= 1
