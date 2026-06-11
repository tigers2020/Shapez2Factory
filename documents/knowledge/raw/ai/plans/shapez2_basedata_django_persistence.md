# shapez2 basedata IVVD — Django canonical persistence (plan)

**Status**: ACTIVE (implementation in progress)  
**Scope**: [`documents/shapez_2_data/basedata-v1137`](../../shapez_2_data/basedata-v1137) only (excludes saves · blueprints).

## Purpose

Treat `shapez_core` as **canonical immutable verified dataset** layer; load game basedata into SQLite/Postgres in a **deterministic · verifiable** form. Tooling apps like `reverse_engineering` **import this layer**; solver/replay reference **core only**.

## App boundary

- **Canonical DB · models**: `django_apps.shapez_core` only.
- **Extraction · runtime scan · Explorer UI**: separate app (e.g. `reverse_engineering`). solver/replay must not import that app.

## Data philosophy

| Stage | Meaning |
|-------|---------|
| Imported | Read raw bytes, `raw_text`/`payload`, `sha256`, `byte_size` |
| Schema | `jsonschema` (only when schema maps to that document) |
| Cross-ref | ID set consistency e.g. `identifiers.json` ↔ `buildings.json` |
| Semantic | Pure rules in `domain/` (when added); minimal stub for now |
| Sealed | `release_integrity_hash` fixed via `shapez-ivvd-seal-v1` payload |

**IMPORT success ≠ validation success**: on structural validation failure still **persist raw/payload** and mark via `ShapezIntegrityIssue` · `schema_valid`, etc.

## Raw policy

- **Default**: preserve full `raw_text` (or equivalent) — reverse engineering · audit trail.
- **Optional**: `compressed_raw_blob` + `raw_compression_codec` — decompressed `sha256` must match uncompressed.
- **Exception mode**: `hash_only_external` only when operationally needed and documented (may omit in initial impl).

## Append-only · Sealed

- After Sealed, **no rewrite of document/identifier rows** (operational principle).
- Re-validation: new `ShapezValidationRun`, new `ShapezIntegrityIssue`.
- **Logical replacement**: mark prior issues in same phase superseded via `ShapezIntegrityIssue.is_superseded`, `superseded_by_run` (no row delete).

### Supersession batch rule (default impl)

When a new `ShapezValidationRun` for same `release` · same `validation_phase` **ends successfully**, set `is_superseded=True`, `superseded_by_run=new run` on issues from **previous run** of that phase where `is_superseded=False`.

## Seal — `shapez-ivvd-seal-v1`

- Constant: `SEAL_ALGORITHM = "shapez-ivvd-seal-v1"`.
- Payload (concept): `algorithm_version`, `game_version`, `document_count`, `documents` (each `source_relative_path`, `sha256`, `byte_size` — **`source_relative_path` ascending sort**, no duplicate paths).
- Serialization: UTF-8, JSON `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`.
- `release_integrity_hash` = SHA-256(hex) of canonical string above.
- Store canonical string in `ShapezBasedataRelease.seal_input_canonical_json` (recompute · debug).

## Coordinate domain

- [`django_apps/shapez_core/domain/coordinates/`](../../django_apps/shapez_core/domain/coordinates/): `raw`/`server` axes, no `x==0` rule, adjacent normalization, etc. — **single source** to extend for replay · reconstruction · topology. Initially module stub · doc strings only.

## Derived lineage

- `ShapezCanonicalArtifact`: track raw → graph → topology … via `source_document`, `derivation_step`, `parent_artifact`. Initial schema only.

## Management command

- `python manage.py import_shapez_basedata --root <path> [--replace] [--strict-seal]`
- `--replace`: if same `game_version` release exists, delete and reload.
- `--strict-seal`: non-zero exit if error-level issues before seal (optional).

## Settings

- `SHAPEZ_BASEDATA_ROOT`: default `BASE_DIR / "documents/shapez_2_data/basedata-v1137"`.

## External references

- [Zuplo — JSON Schema validation](https://zuplo.com/blog/verify-json-schema/)
- [W3C VC JSON Schema](https://www.w3.org/TR/vc-json-schema/)

## Approval

This document is an ACTIVE plan for implementation alignment. On CANON promotion, update `documents/index/document_inventory.md`.
