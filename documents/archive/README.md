# `documents/archive/`

완료·폐기·대체·보관 문서를 모아 둔다. 현재 구현 판단은 archive가 아니라 [`documents/index/document_inventory.md`](../index/document_inventory.md)와 `CANON` 문서를 우선한다.

## Archive buckets

| 하위 경로 | 상태 | 설명 |
|------|------|------|
| [`2026-05-completed/`](2026-05-completed/README.md) | `COMPLETED` | 2026-05에 완료 처리된 Python 정리·Recipe Graph Editor 계열 문서 묶음. |
| [`completed-implementation/`](completed-implementation/README.md) | `COMPLETED` | 구현 반영이 끝난 `plan_*`/`research_*` 1:1 pair를 stem별로 보관한다. |
| [`obsolete-src-shapez2-solver-plans-2026-05-01/`](obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | Django-first 전환 전 `src/shapez2_solver` 기준의 오래된 계획 초안. |
| [`2026-05-orphan-mining-layout-plans-after-app-removal/`](2026-05-orphan-mining-layout-plans-after-app-removal/README.md) | `ARCHIVED` | 채굴 솔버 제거 후 전제 코드 없이 남은 placement 관련 플랜 3건. 구현 근거로 사용 금지. |
| [`refactor_audit_pre_mining_solver_removal_2026-05/`](refactor_audit_pre_mining_solver_removal_2026-05/README.md) | `ARCHIVED` | 제거된 `mining_solver_cursor_sessions` 정본을 인용한 감사 보고 묶음. 역사 전용. |

## 2026-05-15 archive 판정

- `django_apps.shapez_asteroid` 및 채굴 레이아웃 v2 구현·canonical step 스펙·구 mining archive 트리는 저장소에서 제거되었다. 과거 본문은 **git 기록**을 본다.
- 구현 완료 여부가 명확하지 않은 `documents/plans/` 문서는 active/backlog로 유지한다. archive 이동은 검증 결과나 완료 보고가 있는 stem만 대상으로 한다.
- **2026-05-16**: 채굴 레이아웃 고아 플랜 3건은 [`2026-05-orphan-mining-layout-plans-after-app-removal/`](2026-05-orphan-mining-layout-plans-after-app-removal/README.md)로 이동했고, `documents/refactor_audit/`는 [`refactor_audit_pre_mining_solver_removal_2026-05/`](refactor_audit_pre_mining_solver_removal_2026-05/README.md)로 옮겼다.

상위 지도는 [`../README.md`](../README.md)를 우선한다.
