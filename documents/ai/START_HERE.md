# AI Context Start Here

이 파일은 새 AI 세션·서브에이전트·Cursor 작업이 문서 context를 잡을 때 가장 먼저 읽는 진입점이다.

## 읽기 순서

1. [`../../AGENTS.md`](../../AGENTS.md)
2. [`../index/document_lifecycle.md`](../index/document_lifecycle.md)
3. [`../index/document_inventory.md`](../index/document_inventory.md)
4. 작업 유형별 [`manuals/`](manuals/) 문서
5. 현재 작업의 [`current_plan.md`](current_plan.md)와 [`checklist.md`](checklist.md)
6. 필요한 `CANON` 문서

## Authority 규칙

- `CANON`만 현재 시스템 계약이다.
- `ACTIVE`는 진행 중 플랜이며, 완료 전까지 정본이 아니다.
- `RESEARCH`는 근거·실험이며, 구현 계약이 아니다.
- `REPORT`는 관측·로그 분석이며, 설계 정본이 아니다.
- `ARCHIVED`와 `SUPERSEDED`는 역사 확인용이다. 구현 판단에 쓰지 않는다.

## Solver 작업 기본 canon

채굴 레이아웃 솔버 작업은 먼저 [`../index/document_inventory.md`](../index/document_inventory.md)의 "채굴 레이아웃 솔버 정본 후보" 표를 확인한다.

특히 다음 계약은 오래된 plan/report보다 우선한다.

- pipeline/recovery control flow
- protected corridor lifecycle
- reclaim/recovery boundary
- final validation assertion gate
- replay timeline/cycle contract

## 금지

- `documents/archive/`의 내용을 현재 구현 근거로 사용하지 않는다.
- `documents/debug/`와 진행 보고서를 spec으로 승격하지 않는다.
- competing spec을 발견하면 바로 구현하지 말고 `SUPERSEDED` 후보로 표시하거나 inventory 정리 항목에 남긴다.
- canon을 키우기 위해 실험·TODO·로그 분석을 넣지 않는다. canon은 stable invariant와 contract만 담는다.
