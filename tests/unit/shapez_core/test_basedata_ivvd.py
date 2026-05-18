"""IVVD basedata import, seal, and supersession."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.shapez_core.domain.basedata_seal import SEAL_ALGORITHM, canonical_seal_payload_v1
from django_apps.shapez_core.models import (
    ShapezBasedataRelease,
    ShapezIdentifierCategory,
    ShapezIntegrityIssue,
    ShapezIntegrityIssueCode,
    ShapezIvvdSeverity,
    ShapezValidationRun,
)
from django_apps.shapez_core.services.basedata_import_service import (
    IDENTIFIER_JSON_KEYS,
    import_basedata_bundle,
    supersede_prior_issues_on_success,
)


def test_canonical_seal_payload_v1_is_deterministic() -> None:
    docs = [
        ("b.json", "bb" * 32, 20),
        ("a.json", "aa" * 32, 10),
    ]
    c1, h1 = canonical_seal_payload_v1(game_version=1137, documents=docs)
    c2, h2 = canonical_seal_payload_v1(game_version=1137, documents=list(reversed(docs)))
    assert c1 == c2
    assert h1 == h2
    assert SEAL_ALGORITHM in c1
    assert '"document_count":2' in c1


def _write_minimal_basedata(root: Path, *, game_version: int = 999001) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "version").write_text(str(game_version), encoding="utf-8")
    identifiers = {
        "BuildingVariantIds": ["TestVariant"],
        "BuildingInternalVariantIds": ["TestInternal"],
        "IslandLayoutIds": [],
        "WikiEntryIds": [],
        "ImageIds": [],
        "VideoIds": [],
        "IconIds": [],
    }
    (root / "identifiers.json").write_text(json.dumps(identifiers), encoding="utf-8")
    buildings = [
        {
            "Id": "TestVariant",
            "InternalVariants": [{"Id": "TestInternal", "MirroredDefinitionId": None}],
        }
    ]
    (root / "buildings.json").write_text(json.dumps(buildings), encoding="utf-8")


@pytest.mark.django_db
def test_import_basedata_bundle_idempotent_and_sealed(tmp_path: Path) -> None:
    root = tmp_path / "basedata-v999001"
    _write_minimal_basedata(root, game_version=999001)
    r1 = import_basedata_bundle(root, replace=False)
    assert r1.game_version == 999001
    assert r1.integrity_status_id == ShapezBasedataRelease.IntegrityStatus.SEALED.value
    assert ShapezIdentifierCategory.objects.filter(release=r1).count() == len(IDENTIFIER_JSON_KEYS)
    assert r1.game_identifiers.count() == 2
    for gid in r1.game_identifiers.all():
        assert gid.identifier_category.release_id == r1.pk
    assert len(r1.release_integrity_hash) == 64
    assert r1.seal_algorithm == "shapez-ivvd-seal-v1"
    assert r1.documents.count() >= 3

    with pytest.raises(ValueError, match="already exists"):
        import_basedata_bundle(root, replace=False)

    r2 = import_basedata_bundle(root, replace=True)
    assert r2.pk != r1.pk
    assert r2.release_integrity_hash == r1.release_integrity_hash


@pytest.mark.django_db
def test_strict_seal_raises_on_xref_errors(tmp_path: Path) -> None:
    root = tmp_path / "basedata-bad"
    root.mkdir()
    (root / "version").write_text("999002", encoding="utf-8")
    identifiers = {
        "BuildingVariantIds": [],
        "BuildingInternalVariantIds": [],
        "IslandLayoutIds": [],
        "WikiEntryIds": [],
        "ImageIds": [],
        "VideoIds": [],
        "IconIds": [],
    }
    (root / "identifiers.json").write_text(json.dumps(identifiers), encoding="utf-8")
    buildings = [{"Id": "Orphan", "InternalVariants": []}]
    (root / "buildings.json").write_text(json.dumps(buildings), encoding="utf-8")

    with pytest.raises(ValueError, match="strict_seal"):
        import_basedata_bundle(root, replace=True, strict_seal=True)


@pytest.mark.django_db
def test_supersede_prior_issues_on_success() -> None:
    rel = ShapezBasedataRelease.objects.create(
        game_version=888001,
        notes="t",
        integrity_status_id=ShapezBasedataRelease.IntegrityStatus.IMPORTED.value,
    )
    run1 = ShapezValidationRun.objects.create(
        release=rel,
        validation_phase_id="xref",
        success=True,
        summary_json={},
    )
    run2 = ShapezValidationRun.objects.create(
        release=rel,
        validation_phase_id="xref",
        success=True,
        summary_json={},
    )
    sev = ShapezIvvdSeverity.objects.get(code="error")
    itc, _ = ShapezIntegrityIssueCode.objects.get_or_create(
        code="OLD",
        defaults={"summary": "", "default_severity": sev},
    )
    ShapezIntegrityIssue.objects.create(
        release=rel,
        validation_run=run1,
        issue_type=itc,
        severity=sev,
        message="old",
    )
    n = supersede_prior_issues_on_success(rel, run2)
    assert n == 1
    issue = ShapezIntegrityIssue.objects.get(issue_type_id="OLD")
    assert issue.is_superseded is True
    assert issue.superseded_by_run_id == run2.pk
