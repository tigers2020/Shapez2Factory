---
name: shapez2-harness
description: >-
  shapez2Solver 전체 워크플로·하네스·멀티 페르소나 오케스트레이션. 10단계 파이프라인,
  Persona Dialogue 3단계, 검증 순서를 체크리스트로 적용할 때 사용한다.
disable-model-invocation: true
---

# shapez2 하네스 (오케스트레이션)

롤플레이 확장 없이 **절차만** 따른다. 정본은 [protocols/README.md](../../../protocols/README.md), 구현 중 3단계는 [.cursor/rules/persona-dialogue.mdc](../../rules/persona-dialogue.mdc), 역할 카드는 [persona/README.md](../../../persona/README.md).

채팅에서 이 스킬을 켜려면 `@shapez2-harness` 또는 에이전트/규칙에 이 Skill을 포함한다.

## 시작 전

- [ ] 작업 유형 하나 선택: django · solver · graph UI · frontend · tests · refactor · database
- [ ] [AGENTS.md](../../../AGENTS.md) Manual Routing에 따라 해당 [documents/ai/manuals/*.md](../../../documents/ai/manuals/)만 연다
- [ ] 의미 있는 변경이면: [documents/](../../../documents/)에 리서치·플랜 → **사람 승인** 후에만 코드 수정 ([protocols/README.md](../../../protocols/README.md) 1~5단계)

## 구현 단계 (파이프라인 6번 안에서만)

- [ ] 1. 요약·책임 분배 (`[시몬]`)
- [ ] 2. 담당 한두 문장 (`[도미닉]`·`[유리]`·`[아다]`·`[지나]` 등)
- [ ] 3. 코드 — 2 없이 3 금지

## 마감 순서 (7~10)

- [ ] 7 리뷰어: 기획·포트·유스케이스 정합 (유리 주도, 시몬 보조)
- [ ] 8 QA 테스: 동작·시나리오·경계·증거
- [ ] 9 렉스 하네스: 아래 검증 순서, 실패 시 담당 레이어로 되돌림
- [ ] 10 시몬 최종·문서: 의도·스코프, `documents/` 동기화

## 검증 명령 (렉스 · dual gate)

작업 시작 분류: [`AGENTS.md`](../../../AGENTS.md) § Contract-first SDD.

**반복(구현 중):**

1. narrow **`python -m pytest <path>`** (spec-gated)
2. 필요 시 `ruff` / `mypy` / `black .`(로컬 수정)

**PR·병합·CI(full gate):** [`testing.md`](../../../documents/ai/manuals/testing.md#quality-gate-sequence)

1. `python -m ruff check .`
2. `python -m black --check .`
3. `python -m mypy .`
4. `python -m pytest`

- 통과/실패/미실행을 분리해 보고. `black .` vs `black --check .` 구분.
- 마감 **MUST** [shapez2-core.mdc](../../rules/shapez2-core.mdc) Caveman 6절. 테스트·금지 shortcut: [testing.md](../../../documents/ai/manuals/testing.md).

## 참고 링크

- 다각도 리서치(웹·학술·커뮤니티·교차검증·종합 보고): [research-harness](../research-harness/SKILL.md)
- 종합 코드 리뷰(병렬 감사·통합 리포트): [code-review-harness](../code-review-harness/SKILL.md)
- 데이터 파이프라인 설계(스키마·ETL·검증·모니터링 위임): [data-pipeline-harness](../data-pipeline-harness/SKILL.md)
- Cursor IDE 전용 절차: [cursor-shapez2-harness](../cursor-shapez2-harness/SKILL.md)
- Caveman 출력·긴 세션: [caveman-mode](../caveman-mode/SKILL.md) (`@caveman-mode`)
- 외부 하네스 예시(Claude Code `.claude/`): <https://github.com/dingcodingco/youtube-minsim-with-harness>
