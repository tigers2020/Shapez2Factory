---
name: start-develop
description: >-
  Runs prompt-driven implementation then reconciles
  documents/Algorithm/checklist.md. Use when the user invokes /start_develop,
  @start-develop, or asks to develop then update the Algorithm checklist.
disable-model-invocation: true
---

# start-develop (`/start_develop`)

prompt 대로 개발 후 @documents/Algorithm/checklist.md 리스트 확인 후 체크해.

## 순서

1. **개발**: 현재 대화의 프롬프트·범위에 맞게 구현한다. 프로젝트 규칙은 이미 로드된 [AGENTS.md](../../../AGENTS.md)·[root.mdc](../../rules/root.mdc)·[persona-dialogue.mdc](../../rules/persona-dialogue.mdc)를 따른다. 플랜 게이트가 있으면 승인 전 구현하지 않는다.
2. **검증**: 변경 범위에 맞게 `python -m pytest`(또는 영향 경로)·가능하면 `ruff` / `mypy` / `black`을 돌리고, 실패·미실행은 보고에 남긴다.
3. **체크리스트**: [documents/Algorithm/checklist.md](../../../documents/Algorithm/checklist.md)를 연다.
4. **체크 반영**: 이번 작업으로 **실제로 충족된** 항목만 `- [ ]` → `- [x]`로 바꾼다. 파일에 이미 있는 `(확인)`·주석(`//`) 패턴이 있으면 그 줄의 스타일을 맞춘다.
5. **범위 밖 금지**: 이번 프롬프트와 무관한 항목·수동(PR)·가정 항목을 추측으로 체크하지 않는다.

## 참고

- 알고리즘 체크리스트 정본 위치: `documents/Algorithm/checklist.md` (Solver v2 등 시퀀스별 `- [ ]`/`- [x]`).
- 전역 AI 작업 체크리스트와 혼동하지 않는다: `documents/ai/checklist.md`는 별도 파일이다.
