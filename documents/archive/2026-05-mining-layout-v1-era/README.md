# Mining layout v1-era archive (2026-05)

## 목적

이 archive는 현재 구현 권위에서 내려온 `asteroid_mining_layout` v1 시대 문서를 보관한다. 포함 대상은 v1 패키지 경로, v1 refactory 메모, Algorithm root 메모, 일부 v1 plans/research/reports/ai plans다.

현재 구현 권위는 `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/`와 `documents/Algorithm/mining_solver_cursor_sessions/`다. 이 archive의 문서는 역사 확인과 회귀 맥락 확인용이며 현재 설계 판단의 정본으로 쓰지 않는다.

## 상태

| 상태 | 의미 |
|------|------|
| `ARCHIVED` | 현재 설계 판단·구현 계약의 정본이 아니다. |

상태 정의는 [`documents/index/document_lifecycle.md`](../../index/document_lifecycle.md)를 따른다.

## 하위 폴더

| 경로 | 출처/내용 |
|------|-----------|
| [`refactory/`](refactory/) | 기존 `documents/refactory/` 본문 |
| [`algorithm-root/`](algorithm-root/) | 기존 `documents/Algorithm/*.md` root 문서. `mining_solver_cursor_sessions/`는 제외 |
| [`plans/`](plans/) | v1 경로를 참조하던 계획 문서 |
| [`research/`](research/) | v1 solver/asteroid research 문서 |
| [`reports/`](reports/) | v1-era audit/debug/verification 보고 |
| [`debug/`](debug/) | v1-era debug sample report |
| [`ai-plans/`](ai-plans/) | `documents/ai/plans/` 중 v1-era 계획 |
| [`ai/`](ai/) | `documents/ai/`에서 이동한 v1-era notes/contract snapshots |

## 운영 메모

- `documents/ai/current_plan.md`와 `documents/ai/checklist.md`는 현재 작업 상태를 담을 수 있으므로 이 archive로 이동하지 않는다.
- v2 구현 또는 canonical spec에서 필요한 내용이 있으면 archive 문서를 직접 정본으로 쓰지 말고 `documents/Algorithm/mining_solver_cursor_sessions/`, ADR, 또는 현재 계획 문서에 반영한다.
- 새 archive 이동은 구현 완료 또는 obsolete 근거가 확인된 문서에만 한다.

## 마지막 정리

- 2026-05-14: v1 package era 문서 묶음 archive 분류.
- 2026-05-15: 상위 문서 인덱스와 맞게 archive 역할 설명을 갱신.
