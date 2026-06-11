# Import Pipeline — `raw_type_index.json`

**Prerequisites:** `manifest.json` imported; verify `file_hashes.raw_type_index.json`.

**Role:** Optional **lookup/audit** import — can run parallel to content dumps; not a FK prerequisite for `prefabs`/`asset_references`.

## Stages

1. **Load** — large file (~1.8 MB); stream or batch insert.
2. **Validate** — 6497 rows; required keys; UNIQUE (`type_name`, `assembly_name`).
3. **Normalize** — trim; set flags `is_compiler_generated`, `is_unity_generated` from patterns.
4. **Source metadata** — optional `source_object_record` per index.
5. **Sample evidence** — seed `20260521`, indices 524, 3325, 3710 in audit.
6. **DTO** — `ClrTypeRegistryEntryDTO(type_name, assembly_name, dump_stable_id, flags, source_row_index)`.
7. **Validate DTO** — warn on duplicate `stable_id` with different assemblies (expected 8 clusters).
8. **Upsert** — ON CONFLICT (`type_name`, `assembly_name`) UPDATE `dump_stable_id`, flags.
9. **Children** — none.
10. **Resolve FK** — optional: link `assembly_name` to manifest DLL map.
11. **Invariants** — row count 6497; composite unique; flag counts logged.
12. **Audit** — duplicate `stable_id` report, top assemblies, compiler-generated %.

## Idempotency

Natural key: (`type_name`, `assembly_name`). Same file → same 6497 rows.

## Unknown fields → `unknown_property` only.

## Runtime metadata

- Do not promote `type_name` strings to Django model class names.
- Filter or soft-delete compiler-generated rows for planner-facing views.
