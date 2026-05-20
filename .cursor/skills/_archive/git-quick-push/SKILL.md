---
name: git-quick-push
description: >-
  Stages changes tied to the current work session, commits, and pushes the
  current branch. Use when the user invokes /git-quick-push or @git-quick-push,
  or asks for a quick git add, commit, and push in one go.
disable-model-invocation: true
---

# git-quick-push

워크플로: **연관 파일만 git add → commit → push** (에이전트가 터미널에서 직접 실행).

호출: 채팅에서 `@git-quick-push` 또는 사용자가 `/git-quick-push`라고 부를 때 이 스킬을 연다.

## 절차

저장소 루트(워크스페이스)에서 순서대로 수행한다.

0. 모든 커밋 언어는 한글로 통일한다.

1. **이번 대화·작업과 연관된 경로** `git add <path> …` 한다. 연관 파일은 예를 들어 다음에서 판별한다: 사용자가 명시한 경로, 이번 세션에서 편집·생성된 파일, 같은 기능/이슈에 속하는 호출부·테스트·문서. 불확실하면 사용자에게 한 번 확인한다. 무시 규칙(`.gitignore`)은 Git이 따른다.

2. **`git commit`** — 대화형 에디터를 쓰지 않는다. 커밋 메시지는 다음 우선순위로 정한다.
   - 사용자가 이번 턴에서 메시지를 주었으면 그 문자열을 사용한다.
   - 없으면 `git status`·스테이징된 변경 요약으로 한 줄짜리 메시지를 만든다 (예: `chore: sync local changes` 또는 변경 내용에 맞는 `feat:` / `fix:` / `docs:` 등).

3. 스테이징 후 커밋할 내용이 없으면(`git diff --cached --quiet` 등으로 확인) 커밋 단계는 건너뛰고, 이미 원격보다 앞서 있으면 push만 시도한다.

4. **`git push`** — 현재 브랜치를 upstream으로 푸시한다. upstream이 없으면 `git push -u origin <current-branch>` 형태로 설정한다.

## 보고

- 실행한 명령 요약, 성공/실패, 원격 오류(거절·충돌·권한)가 있으면 그대로 전달한다.
- 커밋을 생략한 경우(변경 없음) 그 이유를 한 줄로 적는다.
