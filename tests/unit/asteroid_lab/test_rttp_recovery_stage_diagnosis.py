"""A1 — RTTP core recovery stage diagnosis."""

from __future__ import annotations

import json
from pathlib import Path

from django_apps.asteroid_lab.contracts.rttp_recovery_stage_diagnosis import (
    FLAG_EXTERIOR_ROUTE_MISSING,
    FLAG_MISSING_EXTENSIONS,
    FLAG_ROUTE_MATERIALIZATION_MISSING,
    FLAG_VALIDATION_FAILED,
    FLAG_VALIDATION_FALSE_POSITIVE,
    STAGE_S2_EXTENSION_GEOMETRY,
    STAGE_S3_ROUTE_MATERIALIZATION,
    STAGE_S6_COMMIT_VALIDATION_GAP,
    SYMPTOM_ROUTE_ZERO_VALIDATION_PASSED,
)
from django_apps.asteroid_lab.services.rttp_recovery_stage_diagnosis import (
    diagnose_recovery_evidence_row,
)


def _a0_primary_row() -> dict[str, object]:
    return {
        "slug": "rttp-core-recovery-test-map",
        "committed_extractor_count": 23,
        "visible_extension_cell_count": 0,
        "committed_output_transport_cells": 14,
        "committed_route_cell_count": 0,
        "exterior_connected_route_count": 0,
        "validation_passed": True,
        "confirmed_count": 23,
    }


def test_a0_baseline_primary_slug_stage_diagnosis() -> None:
    diagnosis = diagnose_recovery_evidence_row(_a0_primary_row())
    assert diagnosis.first_failing_stage == STAGE_S2_EXTENSION_GEOMETRY
    assert STAGE_S2_EXTENSION_GEOMETRY in diagnosis.blocking_stages
    assert STAGE_S3_ROUTE_MATERIALIZATION in diagnosis.blocking_stages
    assert STAGE_S6_COMMIT_VALIDATION_GAP in diagnosis.blocking_stages
    assert FLAG_MISSING_EXTENSIONS in diagnosis.diagnostic_flags
    assert FLAG_ROUTE_MATERIALIZATION_MISSING in diagnosis.diagnostic_flags
    assert FLAG_VALIDATION_FALSE_POSITIVE in diagnosis.diagnostic_flags
    assert diagnosis.primary_symptom == SYMPTOM_ROUTE_ZERO_VALIDATION_PASSED


def test_route_zero_without_validation_pass_is_s3_not_false_positive_only() -> None:
    diagnosis = diagnose_recovery_evidence_row(
        {
            "committed_extractor_count": 5,
            "visible_extension_cell_count": 2,
            "committed_route_cell_count": 0,
            "exterior_connected_route_count": 0,
            "committed_output_transport_cells": 5,
            "validation_passed": False,
        }
    )
    assert diagnosis.first_failing_stage == STAGE_S3_ROUTE_MATERIALIZATION
    assert FLAG_VALIDATION_FALSE_POSITIVE not in diagnosis.diagnostic_flags
    assert FLAG_VALIDATION_FAILED in diagnosis.diagnostic_flags


def test_exterior_missing_when_route_present() -> None:
    diagnosis = diagnose_recovery_evidence_row(
        {
            "committed_extractor_count": 3,
            "visible_extension_cell_count": 1,
            "committed_route_cell_count": 4,
            "exterior_connected_route_count": 0,
            "committed_output_transport_cells": 3,
            "validation_passed": True,
            "installable_shape_field_cell_count": 100,
        }
    )
    assert FLAG_EXTERIOR_ROUTE_MISSING in diagnosis.diagnostic_flags
    assert STAGE_S3_ROUTE_MATERIALIZATION in diagnosis.blocking_stages


def test_frozen_a0_baseline_json_primary_slugs_match_expected_stages() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    baseline_path = (
        repo_root
        / "docs"
        / "superpowers"
        / "reports"
        / "2026-05-30-rttp-core-recovery-evidence-baseline.json"
    )
    if not baseline_path.is_file():
        return
    report = json.loads(baseline_path.read_text(encoding="utf-8"))
    primary_slugs = frozenset(
        {
            "rttp-core-recovery-test-map",
            "rttp-cert-candidate-recon-l0",
        }
    )
    for row in report.get("results") or []:
        slug = str(row.get("slug") or "")
        if slug not in primary_slugs:
            continue
        diagnosis = diagnose_recovery_evidence_row(row)
        assert diagnosis.first_failing_stage == STAGE_S2_EXTENSION_GEOMETRY, slug
        assert "missing_extensions" in diagnosis.diagnostic_flags, slug
