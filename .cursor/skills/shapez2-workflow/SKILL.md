---
name: shapez2-workflow
description: >-
  shapez2Solver 전체 워크플로 오케스트레이션. 10단계 파이프라인 체크리스트,
  Cursor IDE 절차(컨텍스트·MCP·스레드 분리), 검증 dual gate를 한 곳에서 적용한다.
  /shapez2-workflow 또는 @shapez2-workflow 로 호출한다.
disable-model-invocation: true
---

# shapez2 워크플로 (통합 하네스)

정본: [protocols/README.md](../../../protocols/README.md)  
상시 규칙: [shapez2-core.mdc](../../rules/shapez2-core.mdc) · [AGENTS.md](../../../AGENTS.md)  
페르소나 3단계: [persona-dialogue.mdc](../../rules/persona-dialogue.mdc) — **5단계(구현)에서만**

## 시작 전 체크리스트

- [ ] 작업 유형 하나 선택: `django` · `solver` · `graph UI` · `frontend` · `tests` · `refactor` · `database`
- [ ] [AGENTS.md Manual Routing](../../../AGENTS.md#manual-routing)에 따라 해당 `documents/ai/manuals/*.md`만 `@`로 연다
- [ ] `@` 범위 최소화 — 코드베이스 전체·거대 폴더는 피한다
- [ ] 주제가 Pass·Recovery·Replay·routing 등으로 갈리면 스레드 분리 또는 서브에이전트로 격리한다

## 의미 있는 변경 게이트 (protocols 1~5단계)

- [ ] `documents/`에 리서치·플랜 작성
- [ ] **사람 승인** 후에만 코드 수정 — 승인 전 구현 금지

## 구현 단계 (protocols 5번 — 페르소나 3단계 적용)

- [ ] 1. `[시몬]` — 요청 요약·책임 분배
- [ ] 2. `[도미닉]`·`[유리]`·`[아다]`·`[지나]` — 담당 한두 문장
- [ ] 3. 코딩 — **2단계 없이 3단계로 가지 않는다**

## 마감 순서 (protocols 6~10단계)

- [ ] 6 구현 완료
- [ ] 7 리뷰어 — 기획·포트·유스케이스 정합 (유리 주도, 시몬 보조)
- [ ] 8 QA 테스 — 동작·시나리오·경계·증거
- [ ] 9 렉스 하네스 — 아래 검증 게이트 실행
- [ ] 10 시몬 최종·문서 — `documents/` 동기화, [doc-update](../doc-update/SKILL.md)

## 검증 게이트 (렉스)

**반복(구현 중):**
```bash
python -m pytest <narrow path>
python -m ruff check <paths>
```

**PR·병합·CI (full gate):**
```bash
python -m ruff check .
python -m black --check .
python -m mypy src
python -m pytest
```

통과·실패·미실행을 분리해 보고. 마감은 [shapez2-core.mdc Caveman 6절](../../rules/shapez2-core.mdc) 필수.

## MCP

- 로컬 grep·Read로 충분하면 호출하지 않는다
- Serena 사용 시: 호출 전 `initial_instructions` 먼저, 스키마는 `mcps/user-serena/tools/` 확인
- context7: 라이브러리 문서 온디맨드

## 참고 링크

- 테스트·Forbidden: [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md)
- Cursor 습관·컨텍스트: [documents/ai/manuals/cursor_usage.md](../../../documents/ai/manuals/cursor_usage.md)
- Asteroid Lab 불변식: [asteroid-lab-invariants.mdc](../../rules/asteroid-lab-invariants.mdc)
