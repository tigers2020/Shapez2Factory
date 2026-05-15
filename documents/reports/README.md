# Reports 문서 인덱스

이 디렉터리는 실행 관측, 감사, 디버그 분석을 둔다. `REPORT` 문서는 현재 상태의 증거이지만 algorithm 정본은 아니다. 정본으로 승격하려면 `documents/Algorithm/mining_solver_cursor_sessions/`, ADR, 또는 `documents/index/document_inventory.md`에 별도로 반영한다.

## 현재 보고서 묶음

| 경로 | 상태 | 설명 |
|------|------|------|
| [`documentation_audit/`](documentation_audit/README.md) | `REPORT` | 2026-05-15 문서/코드 대조, authority matrix, obsolete 후보, cleanup plan. |
| [`2026-05/`](2026-05/) | `REPORT` | 2026-05 solver 감사·수용 보고서. 정본 계약이 아니라 관측 결과다. |

## 사용 규칙

- 구현 판단은 [`../index/document_inventory.md`](../index/document_inventory.md)의 `CANON` 문서를 먼저 본다.
- report에서 확인한 drift는 바로 구현 계약으로 쓰지 않고, 필요한 경우 canonical spec 또는 ADR로 옮긴다.
- archive 후보 판단은 [`documentation_audit/obsolete_candidates.md`](documentation_audit/obsolete_candidates.md)와 [`../archive/README.md`](../archive/README.md)를 함께 본다.
