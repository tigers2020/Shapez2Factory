# Import metadata unification — no parallel tables

Status: **Approved** (documentation + Django `verbose_name` only; **no** new `GameData*` models).

Early review drafts proposed `GameDataImportRun`, `GameDataSourceFile`, `GameDataIgnoredField`, etc. Those roles are **already** implemented under stable Django class names. Do **not** add parallel tables.

## Canonical name → Django model

| Canonical (schema docs) | Django model | What it is |
| ----------------------- | ------------ | ---------- |
| `game_data_import_batch` | `ImportBatch` | One import **run** per `manifest.json` (UK `manifest_self_hash`) |
| `game_data_artifact_checksum` | `ArtifactChecksum` | Per **source file** SHA / import status (`file_hashes.*`) |
| `export_warning` | `ExportWarning` | Manifest export warning line |
| `export_incomplete_section` | `ExportIncompleteSection` | Manifest incomplete section code |
| `localization_export_status` | `LocalizationExportStatus` | Translations export health (1:1 batch) |
| `source_object_record` | `SourceObject` | Per **JSON row** provenance (`source_file`, `source_row_index`); auxiliary `source_path`, `system_id`, `clr_type` |
| `unknown_property` | `UnknownProperty` | Ignored / unmapped field (preview + hash; `reason_code`, `classification`) |

## Rejected parallel names (do not implement)

| Proposed name | Why rejected | Use instead |
| ------------- | ------------ | ----------- |
| `GameDataImportRun` | Duplicates `ImportBatch` | `ImportBatch` |
| `GameDataSourceFile` | Duplicates per-file gate | `ArtifactChecksum` |
| `GameDataIgnoredField` | Duplicates ignored-field row | `UnknownProperty` |
| `GameDataUnknownFieldOccurrence` | Split concerns already covered | `SimulationSystemParameterKey` + `SimulationSystemParameterOccurrence` (keys only); `UnknownProperty` (values preview) |
| `GameDataSchemaFinding` | Duplicates manifest findings | `ExportWarning`, `ExportIncompleteSection` |
| `ImportAudit` | Misnamed CLR capture | `SimulationClrProvenance` (migration `0011`) |
| Generic `audit_blob` on domain rows | Hides schema drift | Typed tables or `SimulationRuntimeAudit` only |

## Three provenance levels (do not collapse)

```text
ImportBatch          → whole export run (manifest)
ArtifactChecksum     → one JSON file in the bundle
SourceObject         → one array element [i] in that file
```

`GameDataSourceFile` is **not** `SourceObject`: the former is file-level integrity; the latter is row-level index.

## `UnknownProperty` contract

- Row-shaped only: no `audit_blob`, no full JSON value.
- `reason_code` examples: `sim_param_*` (simulation ignores), future per-domain prefixes.
- UK: `(import_batch, owner_model, owner_key, json_path)`.

## Simulation-specific (separate from import run metadata)

| Concern | Table |
| ------- | ----- |
| CLR string | `SimulationClrProvenance` |
| Param key registry | `SimulationSystemParameterKey`, `SimulationSystemParameterOccurrence` |
| Speed config | `SimulationBuffableSpeed`, `SimulationMultipleBeltSpeed` |
| Converter audit rows | `SimulationRuntimeAuditIssue` (no JSONField on domain models) |

## Migration policy

- **Rename Django class** only when the old name is actively misleading (`ImportAudit` → `SimulationClrProvenance`).
- **Keep** `ImportBatch` class name; canonical docs use `game_data_import_batch`.
- Admin UI may say **Import run** / **Source file** via `verbose_name` without ORM renames.
