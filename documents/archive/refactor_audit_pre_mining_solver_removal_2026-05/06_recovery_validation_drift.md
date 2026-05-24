# Recovery / Validation Drift

## canonical baseline

- `11_step8_recovery.md`
- `13_step9_validation.md`
- `03_data_schema_dto.md` §B (`PlacementCommitState`, reason namespace)

## live status

`django_apps/asteroid_lab` has no recovery, rollback lifecycle, or final validation assertion gate in the canonical sense. Closest concepts today:

- issue detection in `snapshots/existing_layout_inspection.py`
- rebuild / retry in `replay_pipeline_service.py`
- `"force=True"` retry in `public_pages.py`

These do not substitute for canonical recovery/validation.

## drift matrix

| File / area | Drift | Why it matters | Canonical refs | Severity | Confidence | Action |
|---|---|---|---|---|---|---|
| `django_apps/asteroid_lab/services/replay_pipeline_service.py` | failures expressed as `status/error_message` strings, not typed recovery | cannot handle retry/rollback lifecycle structurally | `11_step8_recovery.md`, `13_step9_validation.md` | `P1` | High | `rewrite` |
| `django_apps/web/views/public_pages.py` | web view directly decides force rebuild | validation/recovery authority leaks into UI request path | `13_step9_validation.md` | `P1` | High | `isolate` |
| `django_apps/asteroid_lab/snapshots/existing_layout_inspection.py` | risk of issue rows expanding toward validation report role | decode-time inspection and final validation differ in timing | `13_step9_validation.md` §15.5 | `P1` | High | `freeze` |
| `django_apps/asteroid_lab/services/dto.py` | missing reason namespace, FSM type, rollback DTO | risk of string soup when recovery is added later | `03_data_schema_dto.md` §B | `P1` | High | `migrate` |

## Explicit absence list

- `PlacementCommitState`
- `RecoveryTrigger`
- `CommitReason`
- `RollbackReason`
- `RejectedReason`
- `QUARANTINED_UNROUTED` / `ROUTED_CONFIRMED` lifecycle
- assertion-only `FinalValidationReport`

## Recommended policy

1. Declare canonical recovery/validation as “not implemented” in current `asteroid_lab`.
2. Do not promote inspection issues into final validation namespace.
3. Replace replay rebuild failure with typed result enum; freeze until string-based branching is removed.
