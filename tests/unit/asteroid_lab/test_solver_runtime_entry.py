"""Solver runtime HTTP entry service tests (PR8)."""

from __future__ import annotations

import base64
import gzip
import json
import random

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.runtime_gene_template_source import (
    GeneTemplateSourceKind,
)
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY,
    SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    run_solver_runtime_for_project,
)

pytestmark = pytest.mark.django_db


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _unique_valid_copy() -> str:
    return _encode_v4_copy(
        {
            "V": random.randint(1, 10_000_000),
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                    {"X": 3, "Y": 1, "T": "Layout_ShapeMinerExtension"},
                ],
            },
        }
    )


def _project_with_map_input() -> m.AsteroidProject:
    client = Client()
    client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": _unique_valid_copy()},
        follow=True,
    )
    return m.AsteroidProject.objects.get()


def _seed_minimal_gene_samples(generator_version: str = "exhaustive_sample_gene_v1") -> None:
    """Seed one belt + one pipe solo-extractor sample for entry tests."""
    genes, _ = generate_exhaustive_sample_genes(
        max_extensions=0, transport_kinds=("belt",), generator_version=generator_version
    )
    assert genes
    g = genes[0]
    m.GeneticSample.objects.update_or_create(
        gene_key=g.key,
        defaults={"name": g.name, "code": g.encoded_copy_string, "metadata_json": dict(g.metadata)},
    )


def test_solver_runtime_entry_persists_summary_and_projection_params() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = run_solver_runtime_for_project(int(proj.pk), run_key="entry-persist")
    assert result.ok is True
    assert result.solver_run_id is not None
    assert result.validation_passed is True

    run = m.SolverRun.objects.get(pk=result.solver_run_id)
    assert SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY in run.config_json
    assert SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY in run.config_json
    summary = run.config_json[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY]
    assert "capacity_satisfied" in summary
    assert "run_success" in summary
    if summary.get("run_success"):
        assert run.status == m.SolverRun.RunStatus.COMPLETED
    elif summary.get("validation_passed"):
        assert run.status == m.SolverRun.RunStatus.PARTIAL
    else:
        assert run.status == m.SolverRun.RunStatus.FAILED
    assert len(result.lab_replay_frames_json) >= 1
    assert isinstance(result.replay_track_metrics, dict)


def test_solver_runtime_entry_persists_gene_template_source() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    result = run_solver_runtime_for_project(int(proj.pk), run_key="entry-gene-source")
    assert result.ok is True

    run = m.SolverRun.objects.get(pk=result.solver_run_id)
    assert SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY in run.config_json
    src = run.config_json[SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY]
    assert src["source"] == GeneTemplateSourceKind.GENETIC_SAMPLE_DB.value
    assert src["gene_count"] >= 1
    assert isinstance(src["gene_ids"], list)

    assert result.gene_template_source["source"] == GeneTemplateSourceKind.GENETIC_SAMPLE_DB.value


def test_solver_runtime_entry_does_not_create_lab_replay_frames() -> None:
    _seed_minimal_gene_samples()
    proj = _project_with_map_input()
    lab_count = m.ReplayFrame.objects.filter(replay_track__project=proj).count()
    run_solver_runtime_for_project(int(proj.pk))
    assert m.ReplayFrame.objects.filter(replay_track__project=proj).count() == lab_count


def test_solver_runtime_entry_requires_map_input() -> None:
    proj = m.AsteroidProject.objects.create(name="Empty", slug="entry-no-inp")
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.NO_MAP_INPUT


def test_solver_runtime_entry_fails_when_no_gene_templates_in_db() -> None:
    """If DB has no seeded GeneticSample rows, entry returns NO_GENE_TEMPLATES_IN_DB."""
    proj = _project_with_map_input()
    # DB is empty (django_db gives clean state per test)
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.NO_GENE_TEMPLATES_IN_DB
