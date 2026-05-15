# `documents/` 인덱스

프로젝트 Markdown 본문은 한국어를 기본으로 한다. 코드, 경로, CLI, 식별자, URL은 원문을 유지한다.

## 가장 먼저 읽을 문서

1. [`README.md`](README.md) — 이 문서. 문서 권위와 읽는 순서.
2. [`Algorithm/mining_solver_cursor_sessions/README.md`](Algorithm/mining_solver_cursor_sessions/README.md) — asteroid mining solver canonical step specs.
3. [`Algorithm/README.md`](Algorithm/README.md) — canonical step order 요약.
4. [`ai/START_HERE.md`](ai/START_HERE.md) — AI 작업 세션 진입점.
5. [`index/document_lifecycle.md`](index/document_lifecycle.md), [`index/document_inventory.md`](index/document_inventory.md) — 문서 lifecycle과 기존 inventory.
6. [`reports/documentation_audit/README.md`](reports/documentation_audit/README.md) — 2026-05-15 문서 감사 결과.

## 권위 계층

| 범주 | 경로 | 사용 규칙 |
|---|---|---|
| canonical algorithm spec | [`Algorithm/mining_solver_cursor_sessions/`](Algorithm/mining_solver_cursor_sessions/README.md) | solver 동작 판단의 1차 정본. canonical docs가 구현보다 우선한다. |
| canonical routing/index | [`README.md`](README.md), [`Algorithm/README.md`](Algorithm/README.md), [`index/`](index/) | 문서 위치와 lifecycle 판단에 사용한다. |
| AI workflow/manuals | [`ai/`](ai/) | 작업 절차, current plan, checklist, manual routing. algorithm spec을 대체하지 않는다. |
| implementation planning | [`plans/`](plans/), [`ai/plans/`](ai/plans/) | 승인된 작업 범위와 backlog 확인용. 정본 충돌 시 정본이 우선한다. |
| audit/report/research | [`reports/`](reports/), [`research/`](research/), [`notes/`](notes/), [`debug/`](debug/) | 관측 증거와 분석. historical report는 current truth가 아니다. |
| historical/obsolete | [`archive/`](archive/), [`refactory/`](refactory/) | 역사 확인용. 현재 구현 판단에 직접 사용하지 않는다. |
| generated/sample output | [`samples/`](samples/), `var/`, root `v2_behavior_artifact_*.json` | output evidence only. 알고리즘 입력으로 사용 금지. |

## canonical solver 문서

현재 asteroid mining solver 정본은 [`Algorithm/mining_solver_cursor_sessions/`](Algorithm/mining_solver_cursor_sessions/README.md)의 README와 01-14 문서다. 특히 다음 원칙은 전역 규칙이다.

- 로그, NDJSON, replay_events, solver_summary는 output evidence only이며 algorithm input이 아니다.
- ExistingLayoutAnalysis는 read-only context다.
- `mineable_placement_cells`는 STEP 1 reconstruction의 산출이다.
- Pass1/Pass2는 provisional placement만 만든다.
- STEP4가 route confirmation을 소유한다.
- Final validation은 assertion-only다.
- Recovery는 bounded branch이며 항상 linear로 실행되는 단계가 아니다.

## 구현 계획과 보고서 사용법

- `plans/`와 `ai/plans/`는 구현 전/중 계획이다. 완료되었거나 v1-era인 문서는 archive 후보로 검토한다.
- `reports/`와 `research/`는 증거와 판단 기록이다. canonical spec으로 승격하려면 Algorithm spec 또는 ADR에 별도로 반영해야 한다.
- `documents/reports/documentation_audit/`는 2026-05-15 기준 문서 감사 결과이며 `REPORT`다.

## future AI coding agents 금지 사항

- `var/*.ndjson`, `latest.ndjson`, replay output, behavior artifact JSON, solver_summary를 읽어 solver algorithm input으로 사용하지 않는다.
- `archive/2026-05-mining-layout-v1-era/`의 v1 경로와 결론을 current v2 구현 계약으로 사용하지 않는다.
- historical report를 조용히 current spec에 병합하지 않는다. 충돌하면 drift/obsolete로 표시한다.
- production code나 solver behavior는 문서 감사 작업에서 수정하지 않는다.
