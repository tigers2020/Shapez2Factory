# `documents/` 인덱스

프로젝트 Markdown 본문은 한국어를 기본으로 한다. 코드, 경로, CLI, 식별자, URL은 원문을 유지한다.

## 가장 먼저 읽을 문서

1. [`README.md`](README.md) — 이 문서. 문서 권위와 읽는 순서.
2. [`Algorithm/README.md`](Algorithm/README.md) — algorithm 문서 슬롯(현재 채굴 솔버 정본 없음).
3. [`ai/START_HERE.md`](ai/START_HERE.md) — AI 작업 세션 진입점.
4. [`index/document_lifecycle.md`](index/document_lifecycle.md), [`index/document_inventory.md`](index/document_inventory.md) — 문서 lifecycle과 inventory.
5. [`reports/README.md`](reports/README.md) — 보고서 묶음 인덱스.

## 권위 계층

| 범위 | 경로 | 사용 규칙 |
|---|---|---|
| domain / workflow 정본 | [`game_rules/`](game_rules/), [`research/`](research/) 중 승격 문서, [`adr/`](adr/), 루트 규칙 파일 | 구현·플랜과 충돌 시 여기를 우선한다. |
| canonical routing/index | [`README.md`](README.md), [`Algorithm/README.md`](Algorithm/README.md), [`index/`](index/) | 문서 위치와 lifecycle 판단에 사용한다. |
| AI workflow/manuals | [`ai/`](ai/) | 작업 절차, current plan, checklist, manual routing. |
| implementation planning | [`plans/`](plans/), [`ai/plans/`](ai/plans/) | 승인된 작업 범위와 backlog 확인용. 정본 충돌 시 정본이 우선한다. |
| audit/report/research | [`reports/`](reports/README.md), [`research/`](research/), [`notes/`](notes/), [`debug/`](debug/)(슬롯·파일 없을 수 있음), [`archive/refactor_audit_pre_mining_solver_removal_2026-05/`](archive/refactor_audit_pre_mining_solver_removal_2026-05/README.md) | 관측 증거와 분석. historical report는 current truth가 아니다. 감사 묶음은 제거된 정본을 인용할 수 있으므로 archive만 본다. |
| historical/obsolete | [`archive/`](archive/), [`refactory/`](refactory/) | 역사 확인용. 현재 구현 판단에 직접 사용하지 않는다. |
| generated/sample output | [`samples/`](samples/), `var/` | output evidence only. 알고리즘 입력으로 사용 금지. |

## 구현 계획과 보고서 사용법

- `plans/`와 `ai/plans/`는 구현 전/중 계획이다. 완료되었거나 obsolete인 문서는 archive 후보로 검토한다.
- `reports/`와 `research/`는 증거와 판단 기록이다. 정본으로 승격하려면 ADR·game_rules·research 승격 절차를 따른다.
- `documents/reports/README.md`는 report 묶음의 현재 라우팅 인덱스다.

## future AI coding agents 금지 사항

- `var/*.ndjson`, replay output, solver_summary를 읽어 **레시피 솔버** 알고리즘 입력으로 사용하지 않는다.
- 과거 mining layout·asteroid 관련 archive/plan 본문은 **git 기록**으로만 본다. 현재 앱 구현 계약으로 쓰지 않는다.
- historical report를 조용히 current spec에 병합하지 않는다. 충돌하면 drift/obsolete로 표시한다.
