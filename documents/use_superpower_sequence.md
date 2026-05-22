Role: Workflow Architect

맞습니다. **`/superpowers:brainstorm`, `/superpowers:write-plan`, `/superpowers:execute-plan` 식 설명은 이 커밋 기준으로는 outdated**입니다.
지정한 `b7a8f769...` 트리 기준으로 보면 `commands/`에는 3개만 있고, 셋 다 **Deprecated** 처리되어 있습니다. 각각 새 방식으로 `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:executing-plans` skill을 쓰라고 되어 있습니다. ([GitHub][1])

## 1. Cursor 설치

Cursor Agent chat에서:

```text
/add-plugin superpowers
```

README 기준 Cursor 설치 명령은 이게 맞습니다. Marketplace에서 `superpowers` 검색도 가능하다고 되어 있습니다. ([GitHub][2])

---

## 2. 현재 방식의 핵심

이 커밋 기준 Superpowers는 “명령어를 직접 치는 도구”라기보다:

```text
설치된 plugin이 skills / agents / commands / hooks를 제공
↓
agent가 상황에 맞는 skill을 호출
↓
필요하면 사용자가 특정 skill 사용을 명시
```

구조입니다. Cursor plugin manifest에도 `skills`, `agents`, `commands`, `hooks` 경로가 등록되어 있습니다. ([GitHub][3])

그리고 README도 “skills trigger automatically”라서 특별한 일을 하지 않아도 된다고 설명합니다. 설치 확인도 `help me plan this feature` 또는 `let's debug this issue`처럼 말해서 관련 skill이 자동 호출되는지 보면 됩니다. ([GitHub][2])

---

## 3. 실제 사용 문장

### 새 기능 / 큰 수정

```text
Use the superpowers:brainstorming skill.

I want to build [기능 설명].
Do not write code yet.
Start by understanding the goal, asking questions, and proposing design options.
```

그 다음 설계 승인 후:

```text
Use the superpowers:writing-plans skill to create an implementation plan from the approved design.
```

계획 승인 후:

```text
Use the superpowers:executing-plans skill to execute this plan task by task.
```

### 버그 수정

```text
Use the superpowers:systematic-debugging skill.

Investigate this bug without jumping straight to a fix.
Find the root cause first, then propose the fix and verification.
```

### 구현 완료 전 검증

```text
Use the superpowers:verification-before-completion skill.

Verify this is actually fixed before saying the task is complete.
```

### 브랜치 마무리

```text
Use the superpowers:finishing-a-development-branch skill.

Run the required verification, then present merge / PR / keep / discard options.
```

---

## 4. 일반 사용 순서

README의 Basic Workflow 기준 순서는 다음입니다. ([GitHub][2])

```text
1. superpowers:brainstorming
2. superpowers:using-git-worktrees
3. superpowers:writing-plans
4. superpowers:subagent-driven-development
   또는 superpowers:executing-plans
5. superpowers:test-driven-development
6. superpowers:requesting-code-review
7. superpowers:finishing-a-development-branch
```

실제로는 이렇게 씁니다:

```text
"Use superpowers:brainstorming for this feature."
↓
설계 승인
↓
"Use superpowers:writing-plans."
↓
계획 승인
↓
"Use superpowers:subagent-driven-development to implement it."
```

서브에이전트가 없거나 Cursor 환경에서 제한이 있으면:

```text
"Use superpowers:executing-plans instead."
```

---

## 5. 현재 skill 목록

지정한 커밋의 `skills/` 디렉터리 기준 목록입니다. ([GitHub][4])

| Skill                            | 용도                        |
| -------------------------------- | ------------------------- |
| `using-superpowers`              | skill 시스템 사용 규칙           |
| `brainstorming`                  | 구현 전 요구사항/설계 확정           |
| `writing-plans`                  | 승인된 설계를 구현 계획으로 변환        |
| `executing-plans`                | 계획을 순서대로 실행               |
| `subagent-driven-development`    | task별 subagent 실행 + 리뷰    |
| `test-driven-development`        | RED-GREEN-REFACTOR 강제     |
| `systematic-debugging`           | 원인 분석 기반 디버깅              |
| `verification-before-completion` | 완료 선언 전 검증                |
| `requesting-code-review`         | 코드 리뷰 요청 전 체크             |
| `receiving-code-review`          | 리뷰 피드백 반영                 |
| `using-git-worktrees`            | 독립 worktree/branch 작업     |
| `dispatching-parallel-agents`    | 병렬 subagent 작업            |
| `finishing-a-development-branch` | merge/PR/keep/discard 마무리 |
| `writing-skills`                 | 새 skill 작성                |

---

## 6. 중요한 정정

### 예전식

```text
/superpowers:brainstorm
/superpowers:write-plan
/superpowers:execute-plan
```

### 현재 커밋 기준 권장식

```text
Use superpowers:brainstorming.
Use superpowers:writing-plans.
Use superpowers:executing-plans.
```

`commands/brainstorm.md`, `commands/write-plan.md`, `commands/execute-plan.md`는 모두 “deprecated”이며 다음 major release에서 제거될 예정이라고 되어 있습니다. ([GitHub][5])

---

## 결론

현재 기준으로는 **slash command를 외워 쓰는 방식이 아니라, skill 이름을 직접 지시하거나 자동 트리거되게 하는 방식**이 맞습니다.

최소로 외울 것은 이 5개입니다:

```text
superpowers:brainstorming
superpowers:writing-plans
superpowers:executing-plans
superpowers:systematic-debugging
superpowers:verification-before-completion
```

그리고 오래된 3개는 쓰지 않는 게 맞습니다:

```text
/superpowers:brainstorm
/superpowers:write-plan
/superpowers:execute-plan
```

[1]: https://github.com/obra/superpowers/tree/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/commands "superpowers/commands at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
[2]: https://github.com/obra/superpowers/tree/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 "GitHub - obra/superpowers at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · GitHub"
[3]: https://github.com/obra/superpowers/blob/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/.cursor-plugin/plugin.json "superpowers/.cursor-plugin/plugin.json at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
[4]: https://github.com/obra/superpowers/tree/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/skills "superpowers/skills at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
[5]: https://github.com/obra/superpowers/blob/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/commands/brainstorm.md "superpowers/commands/brainstorm.md at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
