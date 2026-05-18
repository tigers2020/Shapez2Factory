"""Import and validate shapez2 basedata bundles (IVVD pipeline)."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import cast

import jsonschema  # type: ignore[import-untyped]
from django.db import transaction
from django.utils import timezone

from django_apps.shapez_core.domain.basedata_seal import canonical_seal_payload_v1
from django_apps.shapez_core.lab_sprite_path import resolve_sprite_static_relpath
from django_apps.shapez_core.models import (
    ShapezBasedataDocument,
    ShapezBasedataRelease,
    ShapezCanonicalArtifact,
    ShapezGameIdentifier,
    ShapezIdentifierCategory,
    ShapezIntegrityIssue,
    ShapezIntegrityIssueCode,
    ShapezIvvdArtifactType,
    ShapezIvvdDocumentKind,
    ShapezIvvdLifecycleStatus,
    ShapezIvvdSeverity,
    ShapezValidationRun,
)

IDENTIFIER_JSON_KEYS: frozenset[str] = frozenset(
    {
        "BuildingVariantIds",
        "BuildingInternalVariantIds",
        "IslandLayoutIds",
        "WikiEntryIds",
        "ImageIds",
        "VideoIds",
        "IconIds",
    }
)

SCHEMA_FILENAME_BY_KIND: dict[str, str] = {
    ShapezBasedataDocument.Kind.SCENARIO.value: "ScenarioSchema.schema.json",
    ShapezBasedataDocument.Kind.DIFFICULTY_PRESET.value: "DifficultyPresetSchema.schema.json",
    ShapezBasedataDocument.Kind.SCENARIO_PARAMETER_PRESET.value: (
        "ScenarioParametersPresetSchema.schema.json"
    ),
}

PHASE_SCHEMA = "schema"
PHASE_XREF = "xref"
PHASE_SEMANTIC = "semantic"


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _read_game_version(root: Path) -> int:
    vpath = root / "version"
    if not vpath.is_file():
        msg = f"missing version file: {vpath}"
        raise FileNotFoundError(msg)
    return int(vpath.read_text(encoding="utf-8").strip())


def _iter_document_files(root: Path) -> Iterator[tuple[Path, str, str]]:
    """Yield ``(absolute_path, kind_code, logical_key)``.

    ``kind_code`` matches ``ShapezBasedataDocument.Kind`` string values.
    """

    vfile = root / "version"
    if vfile.is_file():
        yield vfile, ShapezBasedataDocument.Kind.VERSION.value, ""
    yield root / "identifiers.json", ShapezBasedataDocument.Kind.IDENTIFIERS.value, ""
    yield root / "buildings.json", ShapezBasedataDocument.Kind.BUILDINGS.value, ""
    trans = root / "translations-en-US.json"
    if trans.is_file():
        yield trans, ShapezBasedataDocument.Kind.TRANSLATIONS.value, "en-US"

    scenarios = root / "scenarios"
    if scenarios.is_dir():
        for p in sorted(scenarios.glob("*.json")):
            yield p, ShapezBasedataDocument.Kind.SCENARIO.value, p.stem

    for sub, kind in (
        ("difficulty-presets", ShapezBasedataDocument.Kind.DIFFICULTY_PRESET.value),
        ("scenario-parameter-presets", ShapezBasedataDocument.Kind.SCENARIO_PARAMETER_PRESET.value),
    ):
        d = root / sub
        if d.is_dir():
            for p in sorted(d.glob("*.json")):
                yield p, kind, p.stem

    schemas = root / "json-schemas"
    if schemas.is_dir():
        for p in sorted(schemas.glob("*.schema.json")):
            yield p, ShapezBasedataDocument.Kind.JSON_SCHEMA.value, p.name


def _load_schema(root: Path, filename: str) -> dict[str, object] | None:
    p = root / "json-schemas" / filename
    if not p.is_file():
        return None
    raw: object = json.loads(p.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else None


def _issue_code_resolver() -> Callable[[str], ShapezIntegrityIssueCode]:
    memo: dict[str, ShapezIntegrityIssueCode] = {}

    def resolve(code: str, *, default_severity: str = "error") -> ShapezIntegrityIssueCode:
        if code not in memo:
            sev = ShapezIvvdSeverity.objects.get(code=default_severity)
            o, _ = ShapezIntegrityIssueCode.objects.get_or_create(
                code=code,
                defaults={"summary": "", "default_severity": sev},
            )
            memo[code] = o
        return memo[code]

    return resolve


def _validate_identifiers_payload(
    release: ShapezBasedataRelease,
    doc: ShapezBasedataDocument,
    run: ShapezValidationRun,
    resolve: Callable[[str], ShapezIntegrityIssueCode],
) -> list[ShapezIntegrityIssue]:
    issues: list[ShapezIntegrityIssue] = []
    payload = doc.payload
    if not isinstance(payload, dict):
        itc = resolve("IDENTIFIERS_NOT_OBJECT")
        issues.append(
            ShapezIntegrityIssue(
                release=release,
                validation_run=run,
                document=doc,
                issue_type=itc,
                severity=itc.default_severity,
                message="identifiers.json payload is not a JSON object.",
            )
        )
        return issues
    unknown = set(payload.keys()) - IDENTIFIER_JSON_KEYS
    if unknown:
        itc = resolve("IDENTIFIERS_UNKNOWN_KEYS")
        issues.append(
            ShapezIntegrityIssue(
                release=release,
                validation_run=run,
                document=doc,
                issue_type=itc,
                severity=itc.default_severity,
                json_path="/",
                message=f"Unexpected keys in identifiers.json: {sorted(unknown)!s}",
            )
        )
    for key in IDENTIFIER_JSON_KEYS:
        if key not in payload:
            itc = resolve("IDENTIFIERS_MISSING_KEY")
            issues.append(
                ShapezIntegrityIssue(
                    release=release,
                    validation_run=run,
                    document=doc,
                    issue_type=itc,
                    severity=itc.default_severity,
                    json_path=f"/{key}",
                    message=f"Missing key {key!r} in identifiers.json.",
                )
            )
            continue
        val = payload[key]
        if not isinstance(val, list):
            itc = resolve("IDENTIFIERS_KEY_NOT_ARRAY")
            issues.append(
                ShapezIntegrityIssue(
                    release=release,
                    validation_run=run,
                    document=doc,
                    issue_type=itc,
                    severity=itc.default_severity,
                    json_path=f"/{key}",
                    message=f"Key {key!r} must be an array of strings.",
                )
            )
            continue
        for i, item in enumerate(val):
            if not isinstance(item, str):
                itc = resolve("IDENTIFIERS_NON_STRING")
                issues.append(
                    ShapezIntegrityIssue(
                        release=release,
                        validation_run=run,
                        document=doc,
                        issue_type=itc,
                        severity=itc.default_severity,
                        json_path=f"/{key}/{i}",
                        message=f"Non-string entry under {key!r} at index {i}.",
                    )
                )
    return issues


def _run_jsonschema_on_document(
    root: Path,
    _release: ShapezBasedataRelease,
    doc: ShapezBasedataDocument,
    _run: ShapezValidationRun,
) -> tuple[bool | None, list[object]]:
    """Return (schema_valid, errors_list). None = skipped (no schema)."""

    fname = SCHEMA_FILENAME_BY_KIND.get(doc.document_kind_id)
    if fname is None:
        return (None, [])
    schema = _load_schema(root, fname)
    if schema is None:
        return (None, [{"message": f"missing schema file {fname}"}])
    try:
        jsonschema.validate(instance=doc.payload, schema=schema)
    except jsonschema.exceptions.SchemaError as exc:
        return (False, [{"message": f"schema error: {exc!s}"}])
    except jsonschema.exceptions.ValidationError as exc:
        return (False, [{"message": str(exc), "path": list(exc.path)}])
    except Exception as exc:  # noqa: BLE001 — unresolved $ref etc.
        return (False, [{"message": f"validation exception: {exc!s}"}])
    return (True, [])


def _xref_buildings_vs_identifiers(
    release: ShapezBasedataRelease,
    identifiers_doc: ShapezBasedataDocument,
    buildings_doc: ShapezBasedataDocument,
    run: ShapezValidationRun,
    resolve: Callable[[str], ShapezIntegrityIssueCode],
) -> list[ShapezIntegrityIssue]:
    issues: list[ShapezIntegrityIssue] = []
    id_payload = identifiers_doc.payload
    if not isinstance(id_payload, dict):
        return issues
    b_payload = buildings_doc.payload
    if not isinstance(b_payload, list):
        itc = resolve("XREF_BUILDINGS_NOT_ARRAY")
        issues.append(
            ShapezIntegrityIssue(
                release=release,
                validation_run=run,
                document=buildings_doc,
                issue_type=itc,
                severity=itc.default_severity,
                message="buildings.json top-level value is not an array.",
            )
        )
        return issues

    b_variant_ids: set[str] = set()
    internal_ids: set[str] = set()
    for i, entry in enumerate(b_payload):
        if not isinstance(entry, dict):
            itc = resolve("XREF_BUILDING_ENTRY_NOT_OBJECT")
            issues.append(
                ShapezIntegrityIssue(
                    release=release,
                    validation_run=run,
                    document=buildings_doc,
                    issue_type=itc,
                    severity=itc.default_severity,
                    json_path=f"/{i}",
                    message=f"buildings.json[{i}] is not an object.",
                )
            )
            continue
        bid = entry.get("Id")
        if not isinstance(bid, str):
            itc = resolve("XREF_BUILDING_MISSING_ID")
            issues.append(
                ShapezIntegrityIssue(
                    release=release,
                    validation_run=run,
                    document=buildings_doc,
                    issue_type=itc,
                    severity=itc.default_severity,
                    json_path=f"/{i}/Id",
                    message=f"buildings.json[{i}] missing string Id.",
                )
            )
            continue
        b_variant_ids.add(bid)
        ivs = entry.get("InternalVariants")
        if not isinstance(ivs, list):
            continue
        for j, iv in enumerate(ivs):
            if not isinstance(iv, dict):
                continue
            iid = iv.get("Id")
            if isinstance(iid, str):
                internal_ids.add(iid)
            mid = iv.get("MirroredDefinitionId")
            if mid is not None and not isinstance(mid, str):
                itc = resolve("XREF_MIRROR_ID_TYPE")
                issues.append(
                    ShapezIntegrityIssue(
                        release=release,
                        validation_run=run,
                        document=buildings_doc,
                        issue_type=itc,
                        severity=itc.default_severity,
                        json_path=f"/{i}/InternalVariants/{j}/MirroredDefinitionId",
                        message="MirroredDefinitionId must be string or null.",
                    )
                )

    listed_variants = {
        str(x) for x in id_payload.get("BuildingVariantIds", []) if isinstance(x, str)
    }
    listed_internals = {
        str(x) for x in id_payload.get("BuildingInternalVariantIds", []) if isinstance(x, str)
    }

    for missing in sorted(b_variant_ids - listed_variants):
        itc = resolve("XREF_BUILDING_ID_NOT_IN_IDENTIFIERS")
        issues.append(
            ShapezIntegrityIssue(
                release=release,
                validation_run=run,
                document=buildings_doc,
                issue_type=itc,
                severity=itc.default_severity,
                related_identifier=missing,
                message=(
                    f"Building variant {missing!r} in buildings.json "
                    "but not in BuildingVariantIds."
                ),
            )
        )
    for extra in sorted(listed_variants - b_variant_ids):
        itc = resolve("XREF_IDENTIFIER_VARIANT_NOT_IN_BUILDINGS")
        issues.append(
            ShapezIntegrityIssue(
                release=release,
                validation_run=run,
                document=identifiers_doc,
                issue_type=itc,
                severity=itc.default_severity,
                related_identifier=extra,
                message=f"BuildingVariantIds lists {extra!r} but no matching buildings.json entry.",
            )
        )

    for missing in sorted(internal_ids - listed_internals):
        itc = resolve("XREF_INTERNAL_ID_NOT_IN_IDENTIFIERS")
        issues.append(
            ShapezIntegrityIssue(
                release=release,
                validation_run=run,
                document=buildings_doc,
                issue_type=itc,
                severity=itc.default_severity,
                related_identifier=missing,
                message=(
                    f"Internal variant {missing!r} in buildings.json "
                    "but not in BuildingInternalVariantIds."
                ),
            )
        )
    for extra in sorted(listed_internals - internal_ids):
        itc = resolve("XREF_IDENTIFIER_INTERNAL_NOT_IN_BUILDINGS")
        issues.append(
            ShapezIntegrityIssue(
                release=release,
                validation_run=run,
                document=identifiers_doc,
                issue_type=itc,
                severity=itc.default_severity,
                related_identifier=extra,
                message=(
                    f"BuildingInternalVariantIds lists {extra!r} " "but not used in buildings.json."
                ),
            )
        )

    # MirroredDefinitionId must resolve when present
    for i, entry in enumerate(b_payload):
        if not isinstance(entry, dict):
            continue
        ivs = entry.get("InternalVariants")
        if not isinstance(ivs, list):
            continue
        for j, iv in enumerate(ivs):
            if not isinstance(iv, dict):
                continue
            mid = iv.get("MirroredDefinitionId")
            if isinstance(mid, str) and mid and mid not in listed_internals:
                itc = resolve("XREF_MIRROR_UNKNOWN_INTERNAL")
                issues.append(
                    ShapezIntegrityIssue(
                        release=release,
                        validation_run=run,
                        document=buildings_doc,
                        issue_type=itc,
                        severity=itc.default_severity,
                        json_path=f"/{i}/InternalVariants/{j}/MirroredDefinitionId",
                        related_identifier=mid,
                        message=(
                            f"MirroredDefinitionId {mid!r} not in " "BuildingInternalVariantIds."
                        ),
                    )
                )
    return issues


def supersede_prior_issues_on_success(
    release: ShapezBasedataRelease, run: ShapezValidationRun
) -> int:
    """Mark older issues for the same phase superseded by ``run``.

    Returns the number of rows updated.
    """

    if not run.success:
        return 0
    return int(
        ShapezIntegrityIssue.objects.filter(
            release=release,
            validation_run__validation_phase=run.validation_phase,
            is_superseded=False,
        )
        .exclude(validation_run=run)
        .update(is_superseded=True, superseded_by_run=run)
    )


def _has_blocking_issues(release: ShapezBasedataRelease) -> bool:
    return bool(
        ShapezIntegrityIssue.objects.filter(
            release=release,
            severity_id=ShapezIntegrityIssue.Severity.ERROR.value,
            is_superseded=False,
        ).exists()
    )


def import_basedata_bundle(
    root: Path,
    *,
    replace: bool = False,
    strict_seal: bool = False,
) -> ShapezBasedataRelease:
    """Read ``root`` (basedata-v1137 layout), persist IVVD rows, seal release."""

    root = root.resolve()
    if not root.is_dir():
        msg = f"basedata root is not a directory: {root}"
        raise FileNotFoundError(msg)

    game_version = _read_game_version(root)
    with transaction.atomic():
        existing = ShapezBasedataRelease.objects.filter(game_version=game_version).first()
        if existing is not None:
            if not replace:
                msg = (
                    f"ShapezBasedataRelease already exists for game_version={game_version}; "
                    "pass replace=True to delete and re-import."
                )
                raise ValueError(msg)
            existing.delete()

        imported_status = ShapezIvvdLifecycleStatus.objects.get(
            pk=ShapezBasedataRelease.IntegrityStatus.IMPORTED.value
        )
        release = ShapezBasedataRelease.objects.create(
            game_version=game_version,
            notes=f"imported_from={root.as_posix()}",
            integrity_status=imported_status,
        )

        documents: list[ShapezBasedataDocument] = []
        for abs_path, kind_code, logical_key in _iter_document_files(root):
            if not abs_path.is_file():
                continue
            raw_bytes = abs_path.read_bytes()
            rel = _rel(root, abs_path)
            text: str
            try:
                text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = ""
                payload: object = {"_decode_error": "non_utf8_binary"}
            else:
                if kind_code == ShapezBasedataDocument.Kind.VERSION.value:
                    payload = {"value": int(text.strip())}
                else:
                    try:
                        payload = json.loads(text)
                    except json.JSONDecodeError as exc:
                        payload = {"_json_error": str(exc)}
            dk = ShapezIvvdDocumentKind.objects.get(pk=kind_code)
            doc = ShapezBasedataDocument(
                release=release,
                document_kind=dk,
                logical_key=logical_key,
                source_relative_path=rel,
                byte_size=len(raw_bytes),
                sha256=_sha256_hex(raw_bytes),
                raw_text=text,
                payload=payload if isinstance(payload, dict | list) else {"value": payload},
            )
            documents.append(doc)

        ShapezBasedataDocument.objects.bulk_create(documents)
        release.document_count = len(documents)
        release.save(update_fields=["document_count"])

        identifiers_doc = release.documents.filter(
            document_kind_id=ShapezBasedataDocument.Kind.IDENTIFIERS.value
        ).first()
        if identifiers_doc is not None and isinstance(identifiers_doc.payload, dict):
            cat_by_key: dict[str, ShapezIdentifierCategory] = {}
            for key in IDENTIFIER_JSON_KEYS:
                cat, _ = ShapezIdentifierCategory.objects.get_or_create(
                    release=release,
                    key=key,
                    defaults={"sort_order": 0, "label": ""},
                )
                cat_by_key[key] = cat
            rows: list[ShapezGameIdentifier] = []
            seen: set[tuple[int, str]] = set()
            for category in IDENTIFIER_JSON_KEYS:
                vals = identifiers_doc.payload.get(category)
                if not isinstance(vals, list):
                    continue
                icat = cat_by_key[category]
                for v in vals:
                    if not isinstance(v, str):
                        continue
                    key = (icat.pk, v)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        ShapezGameIdentifier(
                            release=release,
                            identifier_category=icat,
                            value=v,
                            sprite_static_relpath=resolve_sprite_static_relpath(v),
                        )
                    )
            ShapezGameIdentifier.objects.bulk_create(rows, ignore_conflicts=True)

    _run_validation_phases(root, release, strict_seal=strict_seal)
    return cast(ShapezBasedataRelease, ShapezBasedataRelease.objects.get(pk=release.pk))


def _run_validation_phases(
    root: Path,
    release: ShapezBasedataRelease,
    *,
    strict_seal: bool,
) -> None:
    resolve = _issue_code_resolver()
    t0 = time.monotonic()
    schema_run = ShapezValidationRun.objects.create(
        release=release,
        validation_phase_id=PHASE_SCHEMA,
        success=False,
        validator_version="shapez_core.basedata_import_service",
    )
    schema_ok = True
    with transaction.atomic():
        for doc in release.documents.select_for_update().order_by("source_relative_path"):
            if doc.document_kind_id == ShapezBasedataDocument.Kind.IDENTIFIERS.value:
                id_issues = _validate_identifiers_payload(release, doc, schema_run, resolve)
                if id_issues:
                    ShapezIntegrityIssue.objects.bulk_create(id_issues)
                doc.schema_validation_errors = [i.message for i in id_issues]
                doc.schema_valid = len(id_issues) == 0
                if id_issues:
                    schema_ok = False
                doc.validated_at = timezone.now()
                doc.save(
                    update_fields=[
                        "schema_valid",
                        "schema_validation_errors",
                        "validated_at",
                    ]
                )
                continue

            valid, errors = _run_jsonschema_on_document(root, release, doc, schema_run)
            doc.schema_validation_errors = errors if isinstance(errors, list) else list(errors)
            doc.validated_at = timezone.now()
            if valid is None:
                doc.schema_valid = None
            else:
                doc.schema_valid = valid
                if not valid:
                    schema_ok = False
            doc.save(
                update_fields=[
                    "schema_valid",
                    "schema_validation_errors",
                    "validated_at",
                    "schema_version",
                ]
            )
            if valid is False:
                itc_schema = resolve("SCHEMA_VALIDATION_FAILED")
                for err in errors:
                    if isinstance(err, str):
                        msg = err
                    elif isinstance(err, dict):
                        msg = str(err.get("message", err))
                    else:
                        msg = str(err)
                    ShapezIntegrityIssue.objects.create(
                        release=release,
                        validation_run=schema_run,
                        document=doc,
                        issue_type=itc_schema,
                        severity=itc_schema.default_severity,
                        message=msg[:2000],
                    )

        schema_run.duration_ms = int((time.monotonic() - t0) * 1000)
        schema_run.success = (
            schema_ok
            and not ShapezIntegrityIssue.objects.filter(
                validation_run=schema_run,
                severity_id=ShapezIntegrityIssue.Severity.ERROR.value,
            ).exists()
        )
        schema_run.summary_json = {"documents_checked": release.documents.count()}
        schema_run.save(update_fields=["duration_ms", "success", "summary_json"])
        supersede_prior_issues_on_success(release, schema_run)

    t1 = time.monotonic()
    xref_run = ShapezValidationRun.objects.create(
        release=release,
        validation_phase_id=PHASE_XREF,
        success=False,
        validator_version="shapez_core.basedata_import_service",
    )
    identifiers_doc = release.documents.filter(
        document_kind_id=ShapezBasedataDocument.Kind.IDENTIFIERS.value
    ).first()
    buildings_doc = release.documents.filter(
        document_kind_id=ShapezBasedataDocument.Kind.BUILDINGS.value
    ).first()
    with transaction.atomic():
        issues: list[ShapezIntegrityIssue] = []
        if identifiers_doc is None or buildings_doc is None:
            if identifiers_doc is None:
                itc = resolve("XREF_MISSING_IDENTIFIERS")
                issues.append(
                    ShapezIntegrityIssue(
                        release=release,
                        validation_run=xref_run,
                        issue_type=itc,
                        severity=itc.default_severity,
                        message="identifiers.json document missing.",
                    )
                )
            if buildings_doc is None:
                itc = resolve("XREF_MISSING_BUILDINGS")
                issues.append(
                    ShapezIntegrityIssue(
                        release=release,
                        validation_run=xref_run,
                        issue_type=itc,
                        severity=itc.default_severity,
                        message="buildings.json document missing.",
                    )
                )
        else:
            issues.extend(
                _xref_buildings_vs_identifiers(
                    release,
                    identifiers_doc,
                    buildings_doc,
                    xref_run,
                    resolve,
                )
            )
        ShapezIntegrityIssue.objects.bulk_create(issues)
        xref_run.duration_ms = int((time.monotonic() - t1) * 1000)
        xref_run.success = len(issues) == 0
        xref_run.summary_json = {"issue_count": len(issues)}
        xref_run.save(update_fields=["duration_ms", "success", "summary_json"])
        supersede_prior_issues_on_success(release, xref_run)

    t2 = time.monotonic()
    sem_run = ShapezValidationRun.objects.create(
        release=release,
        validation_phase_id=PHASE_SEMANTIC,
        success=True,
        validator_version="shapez_core.basedata_import_service.stub",
        summary_json={
            "note": "semantic rules live in domain/; stub run for pipeline completeness."
        },
    )
    sem_run.duration_ms = int((time.monotonic() - t2) * 1000)
    sem_run.save(update_fields=["duration_ms", "success", "summary_json"])
    supersede_prior_issues_on_success(release, sem_run)

    if strict_seal and _has_blocking_issues(release):
        failed = ShapezIvvdLifecycleStatus.objects.get(
            pk=ShapezBasedataRelease.IntegrityStatus.FAILED.value
        )
        release.integrity_status = failed
        release.save(update_fields=["integrity_status"])
        msg = "strict_seal: unresolved error-level integrity issues remain."
        raise ValueError(msg)

    seal_docs = list(
        release.documents.order_by("source_relative_path").values_list(
            "source_relative_path",
            "sha256",
            "byte_size",
        )
    )
    canonical, digest = canonical_seal_payload_v1(
        game_version=release.game_version,
        documents=[(str(p), str(h), int(sz)) for p, h, sz in seal_docs],
    )
    sealed = ShapezIvvdLifecycleStatus.objects.get(
        pk=ShapezBasedataRelease.IntegrityStatus.SEALED.value
    )
    with transaction.atomic():
        rel = ShapezBasedataRelease.objects.select_for_update().get(pk=release.pk)
        rel.release_integrity_hash = digest
        rel.seal_input_canonical_json = canonical
        rel.seal_algorithm = "shapez-ivvd-seal-v1"
        rel.sealed_at = timezone.now()
        rel.integrity_status = sealed
        rel.save(
            update_fields=[
                "release_integrity_hash",
                "seal_input_canonical_json",
                "seal_algorithm",
                "sealed_at",
                "integrity_status",
            ]
        )

    atype = ShapezIvvdArtifactType.objects.get(pk="ivvd_import_bundle")
    ShapezCanonicalArtifact.objects.create(
        release=release,
        artifact_type=atype,
        derivation_step="import",
        payload={"root": str(root), "document_count": len(seal_docs)},
    )
