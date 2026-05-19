# AGENTS.md

Cursor AI용 **shapez2Solver** 라우팅 허브 ([agents.md](https://agents.md/) 표준).

**역할**: 작업 유형 → 매뉴얼 연결 · 문서 권위 · 승인 금지 목록. 상시 규칙(Caveman·게이트·검증)은 [`.cursor/rules/shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc). 절차·토큰·Cloud VM은 [`documents/ai/manuals/cursor_usage.md`](documents/ai/manuals/cursor_usage.md). 파이프라인 정본: [`protocols/README.md`](protocols/README.md). 스킬: [`shapez2-harness`](.cursor/skills/shapez2-harness/SKILL.md) · [`cursor-shapez2-harness`](.cursor/skills/cursor-shapez2-harness/SKILL.md).

---

## Core

- 변경 전 **영향 파일·호출부** 특정. 작고 검증 가능한 단위 우선.
- 비즈니스 규칙은 뷰/템플릿에 두지 않는다 ([@architecture.mdc](.cursor/rules/architecture.mdc)).
- **Contract-first TDD**: [testing.md](documents/ai/manuals/testing.md) 정본. 반복 = narrow `pytest` 우선; PR·병합 = [testing.md § Quality gate](documents/ai/manuals/testing.md#quality-gate-sequence) full gate.
- 의미 있는 변경: `documents/` 리서치·플랜 → **사람 승인** 후 구현. 진행 중 [`current_plan.md`](documents/ai/current_plan.md) · [`checklist.md`](documents/ai/checklist.md).
- 비밀값은 `.env`/설정만. `documents/` Markdown 본문은 **한국어**.

---

## Development Mode: Contract-first TDD

**기본 흐름**: 계약·불변식·회귀를 테스트로 고정 → 최소 구현 → 게이트 통과. line coverage가 아니라 **다시 발견하기 비싼 계약**을 우선한다.

작업 시작 시 변경 범위를 분류한다(복수 가능):

| 분류 | 테스트·문서 순서 |
|------|------------------|
| **계약 변경** | 테스트·관련 문서 **먼저** |
| **회귀 수정** | 재현 테스트 **먼저** |
| **구현 변경** | 가장 좁은 단위 테스트부터 |
| **리팩터링** | 동작 동일이면 기존 테스트로 충분; 계약 변경 시 테스트 갱신 필수 |
| **문서 변경** | pytest 필수 아님; **코드 계약**을 바꾸면 Caveman **Tests**에 테스트 계획 |
| **UI 변경** | DOM·serialization·JS 또는 fixture 회귀 **먼저** |

**Agent MUST NOT** (요약 — 상세·체크리스트는 [testing.md § Forbidden shortcuts](documents/ai/manuals/testing.md#forbidden-shortcuts)):

- 테스트 삭제·완화만으로 green.
- replay·artifact·metrics를 solver·algorithm **입력**으로 사용.
- `route_domain` 다중 patch (`RouteDomainSnapshotBuilder` 단일 소유).
- validation에 repair logic.
- candidate 순서를 commit order로 사용; candidate reachable을 최종 commit 증명으로 사용.
- optimization 내부 raw↔server 재변환.
- `failure_reason`·`event_type`·`issue_code` 등 **자유 문자열** (enum·const + 테스트 동시 갱신).

Asteroid Lab: [@asteroid-lab-invariants.mdc](.cursor/rules/asteroid-lab-invariants.mdc). TDD 상세: [testing.md](documents/ai/manuals/testing.md).

---

## 문서 Authority

- 시작: [`START_HERE.md`](documents/ai/START_HERE.md) · [`document_inventory.md`](documents/index/document_inventory.md) · [`document_lifecycle.md`](documents/index/document_lifecycle.md).
- `CANON`만 계약. `ACTIVE` 플랜 · `RESEARCH` 근거 · `REPORT` 관측. `ARCHIVED`/`SUPERSEDED`는 역사용.

---

## Manual Routing

| 작업 유형 | 매뉴얼 |
|-----------|--------|
| Django · 뷰 · URL | [django.md](documents/ai/manuals/django.md) |
| 솔버 · `shapez_solver` | [solver.md](documents/ai/manuals/solver.md) |
| 그래프 UI · 노드 시각화 | [graph_ui.md](documents/ai/manuals/graph_ui.md) |
| 템플릿 · 정적 · 프론트 빌드 | [frontend.md](documents/ai/manuals/frontend.md) |
| 테스트 · pytest · TDD · 게이트 | [testing.md](documents/ai/manuals/testing.md) |
| 리팩터 · 최소 침습 | [refactor.md](documents/ai/manuals/refactor.md) |
| DB · 마이그레이션 | [database.md](documents/ai/manuals/database.md) |
| Cursor · 컨텍스트 · Cloud | [cursor_usage.md](documents/ai/manuals/cursor_usage.md) |

인덱스: [`documents/ai/README.md`](documents/ai/README.md). 리서치·코드리뷰·데이터 파이프라인: 해당 harness 스킬 또는 [document_lifecycle.md](documents/index/document_lifecycle.md).

구현·페르소나 3단계: [@persona-dialogue.mdc](.cursor/rules/persona-dialogue.mdc). MCP: [@mcp.mdc](.cursor/rules/mcp.mdc).

---

## 명시적 승인 없이 하지 말 것

대규모 폴더 이동 · DB 스키마/마이그레이션 · 미증명 레거시 삭제 · 솔버 핵심 전면 교체 · 공개 URL/API 계약 깨기.

---

## 참조

| 항목 | 경로 |
|------|------|
| 상시 규칙 | [shapez2-core.mdc](.cursor/rules/shapez2-core.mdc) |
| 레이어·앱 소유 | [architecture.mdc](.cursor/rules/architecture.mdc) |
| AI 허브 | [documents/ai/](documents/ai/) |
| 페르소나 | [persona/](persona/) |
| 게임 근거 | [research_shapez2_game_systems_2026-05-01.md](documents/research/research_shapez2_game_systems_2026-05-01.md) |

우선순위: `AGENTS.md` → `shapez2-core.mdc` → glob 규칙.
