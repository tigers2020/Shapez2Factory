# Protected Corridor Drift

## canonical baseline

- `12_protected_corridor.md`
- `08_step4_routing.md`
- `09_step5_pass3_transport.md`

## live finding

live `django_apps/asteroid_lab` tree에는 protected corridor lifecycle에 해당하는 runtime state, DTO, validation, replay layer가 없다. 관련 문자열, enum, module, test surface가 모두 부재하다.

즉 현재 문제는 "잘못 구현된 corridor"가 아니라 "canonical 핵심 시스템이 live tree에 아예 없음"이다.

## 영향

| Area | Live status | Risk | Severity | Confidence | Action |
|---|---|---|---|---|---|
| routing core | 해당 모듈 없음 | canonical routing refactor 작업을 현재 tree에서 수행할 수 없음 | `P1` | High | `freeze` |
| replay layer | hard/soft corridor overlay 없음 | UI contract가 future corridor state를 담지 못함 | `P1` | High | `migrate` |
| validation layer | corridor invariant 없음 | final validation 확장 시 field naming 충돌 위험 | `P1` | High | `migrate` |
| tests | corridor lifecycle tests 없음 | 후속 구현 시 회귀 기준 부재 | `P2` | High | `test-only` |

## early-phase guidance

- `asteroid_lab`에 corridor 개념을 억지로 삽입하지 않는다.
- 먼저 canonical/live boundary를 재정의한다.
- corridor는 solver runtime 패키지가 실제로 생긴 뒤 별도 namespace로 도입한다.

## freeze note

초기 refactor 단계에서는 `reconstruction/*`, `existing_layout_inspection.py`, `web replay UI`를 corridor placeholder로 재해석하지 말 것. 그렇게 하면 canonical protected corridor와 단순 inspection overlay가 혼동된다.
