# Reports 문서 인덱스

이 디렉터리는 실행 관측, 감사, 디버그 분석을 둔다. `REPORT` 문서는 현재 상태의 증거이지만 정본 계약은 아니다. 정본으로 승격하려면 ADR, `documents/game_rules/`, 또는 `documents/index/document_inventory.md`에 별도로 반영한다.

## 현재 보고서 묶음

하위 디렉터리는 필요할 때만 추가한다. 과거에 두었던 `documentation_audit/`, `2026-05/` 등 일부 묶음은 정리 과정에서 삭제되었을 수 있다 — 경로가 없으면 archive·git 기록을 본다.

### Asteroid Lab (플랜 트리에 둔 REPORT)

- [`../plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md`](../plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md) — 2026-05-17 진행 스냅(`REPORT`). 브랜치 기준 `quality/repository-gate-cleanup`. 인덱스: [`../index/document_inventory.md`](../index/document_inventory.md) Research·Report 표.

## 사용 규칙

- 구현 판단은 [`../index/document_inventory.md`](../index/document_inventory.md)의 `CANON` 문서를 먼저 본다.
- report에서 확인한 drift는 바로 구현 계약으로 쓰지 않고, 필요한 경우 ADR 또는 domain spec으로 옮긴다.
- archive 후보 판단은 [`../archive/README.md`](../archive/README.md)를 본다.
