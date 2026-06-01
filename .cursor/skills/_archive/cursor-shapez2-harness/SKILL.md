---
name: cursor-shapez2-harness
description: >-
  shapez2Solver 작업을 Cursor IDE에서 할 때의 절차: @ 참조·스레드·MCP·검증·체크리스트.
  전체 10단계·페르소나 오케스트레이션은 shapez2-harness 스킬을 따른다.
disable-model-invocation: true
---

# Cursor 전용 하네스

**역할**: Cursor 채팅·Composer·에이전트가 **레포 규칙과 동일한 방향**으로 움직이게 하는 **IDE 측 절차**만 담는다. 비즈니스·솔버 정책의 정본은 [AGENTS.md](../../../AGENTS.md), [`.cursor/rules/shapez2-core.mdc`](../../rules/shapez2-core.mdc), [protocols/README.md](../../../protocols/README.md)다.

**관계**: 전체 워크플로(10단계·3단계 대화·검증 나열)는 [shapez2-harness](../shapez2-harness/SKILL.md) (`@shapez2-harness`). 여기서는 **Cursor에서만 쓰는 습관·도구 순서**를 정리한다.

채팅에서 켜려면 `@cursor-shapez2-harness` 또는 에이전트에 이 Skill을 포함한다.

## 1. 시작 전 (컨텍스트)

- [ ] 작업 유형 하나: django · solver · graph UI · frontend · tests · refactor · database — [AGENTS.md](../../../AGENTS.md) Manual Routing → 해당 [documents/ai/manuals/*.md](../../../documents/ai/manuals/)만 `@`로 연다.
- [ ] `@` 범위는 **최소**(필요 파일·폴더만). 코드베이스 전체·거대 폴더는 피한다 ([cursor_usage.md](../../../documents/ai/manuals/cursor_usage.md) 「의도 정밀도」「컨텍스트를 "작업 기억"으로」 절).
- [ ] 주제가 Pass·Recovery·Replay·routing 등으로 갈리면 **스레드 분리** 또는 서브에이전트로 격리한다.

## 2. 게이트 (의미 있는 변경)

- [ ] 리서치·플랜·**사람 승인**이 필요하면 [protocols/README.md](../../../protocols/README.md) 1~5단계를 따르고, 승인 전 코드 수정하지 않는다 ([persona-dialogue.mdc](../../rules/persona-dialogue.mdc)).

## 3. 구현 중 (Cursor 동작)

- [ ] 구현 단계에서는 [persona-dialogue.mdc](../../rules/persona-dialogue.mdc): 요약·분배 → 담당 한두 문장 → 코드(2 없이 3 금지).
- [ ] 터미널·검증은 에이전트가 **직접 실행**하고, 실패 시 대안·재시도 후 보고한다 (사용자 규칙과 정합).
- [ ] 비밀값은 `.env`/설정만; 코드에 하드코딩하지 않는다.

## 4. MCP

- [ ] MCP는 **선택**. 로컬 grep·Read로 충분하면 호출하지 않는다 ([mcp.mdc](../../rules/mcp.mdc)).
- [ ] **Serena**를 쓰기로 했다면, 호출 전 서버 지시대로 **`initial_instructions`** 먼저. 도구 인자는 `mcps/user-serena/tools/` 스키마 확인.

## 5. 마감·검증 (렉스 · dual gate)

작업 분류: [AGENTS.md § Contract-first SDD](../../../AGENTS.md) · [testing.md § Development Mode](../../../documents/ai/manuals/testing.md#development-mode-contract-first-sdd).

**반복:** narrow `python -m pytest <path>` → 필요 시 `ruff` / `mypy` / `black .`

**PR/병합:** [`testing.md` full gate](../../../documents/ai/manuals/testing.md#quality-gate-sequence) — `ruff check .` → `black --check .` → `mypy .` → `python -m pytest`

- [ ] 통과·실패·**미실행**을 분리해 보고. `black .` vs `black --check .` 구분.
- [ ] 단계 작업이면 [`documents/ai/checklist.md`](../../../documents/ai/checklist.md) 반영.

## 6. 완료 보고 (MUST Caveman 6절)

- [ ] [caveman-output.mdc](../../rules/caveman-output.mdc): `Summary` · `Files` · `Contracts` · `Tests` · `Risks` · `Next` (순서·제목 고정).
- [ ] 6절 없이 「완료」 금지. 「완료」는 **## Next**에만.
- [ ] [`checklist.md`](../../../documents/ai/checklist.md) 6절 준수 체크.

긴 replay/DTO 세션 시작 시 `@caveman-mode` 선택.

## 참고

- 온디맨드 철학·토큰·§17: [documents/ai/manuals/cursor_usage.md](../../../documents/ai/manuals/cursor_usage.md)
- [caveman-mode](../caveman-mode/SKILL.md)
- Canvas·SDK 등 다른 Cursor 스킬은 이 레포 `.cursor/skills/`·사용자 스킬 목록을 본다.
