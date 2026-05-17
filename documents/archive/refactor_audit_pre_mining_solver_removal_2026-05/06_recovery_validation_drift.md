# Recovery / Validation Drift

## canonical baseline

- `11_step8_recovery.md`
- `13_step9_validation.md`
- `03_data_schema_dto.md` §B (`PlacementCommitState`, reason namespace)

## live status

`django_apps/asteroid_lab`에는 canonical 의미의 recovery, rollback lifecycle, final validation assertion gate가 없다. 현재 closest concept는:

- `snapshots/existing_layout_inspection.py`의 issue detection
- `replay_pipeline_service.py`의 rebuild / retry
- `public_pages.py`의 `"force=True"` 기반 재시도

이들은 canonical recovery/validation을 대체하지 못한다.

## drift matrix

| File / area | Drift | Why it matters | Canonical refs | Severity | Confidence | Action |
|---|---|---|---|---|---|---|
| `django_apps/asteroid_lab/services/replay_pipeline_service.py` | 실패를 typed recovery가 아니라 `status/error_message` 문자열로 표현 | retry/rollback lifecycle를 구조적으로 다룰 수 없음 | `11_step8_recovery.md`, `13_step9_validation.md` | `P1` | High | `rewrite` |
| `django_apps/web/views/public_pages.py` | web view가 force rebuild를 직접 판단 | validation/recovery authority가 UI request path로 샘 | `13_step9_validation.md` | `P1` | High | `isolate` |
| `django_apps/asteroid_lab/snapshots/existing_layout_inspection.py` | issue rows가 validation report 역할까지 겸하는 방향으로 확장될 위험 | decode-time inspection과 final validation은 시점이 다름 | `13_step9_validation.md` §15.5 | `P1` | High | `freeze` |
| `django_apps/asteroid_lab/services/dto.py` | reason namespace, FSM type, rollback DTO 부재 | 추후 recovery를 붙일 때 string soup로 흘러갈 위험 | `03_data_schema_dto.md` §B | `P1` | High | `migrate` |

## 명시적 부재 목록

- `PlacementCommitState`
- `RecoveryTrigger`
- `CommitReason`
- `RollbackReason`
- `RejectedReason`
- `QUARANTINED_UNROUTED` / `ROUTED_CONFIRMED` lifecycle
- assertion-only `FinalValidationReport`

## 권장 방침

1. 현재 `asteroid_lab`에서는 canonical recovery/validation을 "미구현"으로 선언한다.
2. inspection issues를 final validation namespace로 승격하지 않는다.
3. replay rebuild failure는 typed result enum으로 바꾸고, 문자열 기반 분기 제거 전까지 freeze한다.
