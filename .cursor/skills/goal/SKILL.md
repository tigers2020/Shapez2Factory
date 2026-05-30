---
name: goal
description: >-
  완료 조건(completion condition)을 설정하면 조건이 충족될 때까지 턴을 넘기지 않고
  자율적으로 계속 작업하는 목표 기반 루프. 큰 작업의 검증 가능한 종료 상태(테스트 통과,
  빌드 exit 0, 파일 크기 예산, 이슈 큐 비움 등)를 향해 반복 작업할 때 쓴다.
  `/goal <조건>` 으로 설정, `/goal` 로 상태 확인, `/goal clear` 로 해제한다.
disable-model-invocation: true
---

# /goal — 목표 기반 자율 루프

`/goal` 은 완료 조건을 정하고, 그 조건이 충족될 때까지 매 턴 사용자에게 제어를 돌려주지 않고
계속 작업하게 만든다. 매 작업 단위마다 "조건이 충족됐는가?"를 surfaced 증거(대화·터미널 출력)만으로
평가하고, 충족되면 목표를 자동 해제한다.

Claude Code의 native `/goal`(Stop hook + fast evaluator)은 Cursor에 없으므로, 이 스킬은 동일한
동작을 **상태 파일 + 자율 루프 + 매 턴 자기평가**로 재현한다.

## 언제 쓰나

검증 가능한 종료 상태가 있는 큰 작업:
- 모든 호출 지점이 컴파일되고 테스트가 통과할 때까지 새 API로 모듈 마이그레이션
- 모든 acceptance criteria가 충족될 때까지 설계 문서 구현
- 각 모듈이 크기 예산 아래로 내려갈 때까지 큰 파일 분할
- 큐가 빌 때까지 라벨된 이슈 백로그 처리

## 상태 파일 (단일 진실 공급원)

`var/goal/active_goal.md` 가 세션 간 목표 상태를 보존한다. 형식:

```
status: active            # active | achieved | cleared
condition: <조건 전문>
started_at: <ISO8601>
turns_evaluated: <정수>
last_reason: <평가기의 최근 사유>
```

- **활성 목표는 세션당 하나.** 새 목표를 설정하면 기존 것을 대체한다.
- 매 턴 시작 시 이 파일을 먼저 읽어 활성 목표가 있으면 루프를 이어간다.

## 명령 구문

### 1. 목표 설정 — `/goal <조건>`

1. `var/goal/active_goal.md` 를 `status: active`, 입력한 조건, `started_at`=현재 시각,
   `turns_evaluated: 0`, `last_reason:` 빈 값으로 작성(디렉터리 없으면 생성).
2. **즉시** 조건 자체를 directive로 삼아 작업을 시작한다(별도 프롬프트 불필요).
3. 아래 [동작 루프](#동작-루프)를 따른다.

### 2. 상태 확인 — `/goal` (인자 없음)

`var/goal/active_goal.md` 를 읽어 보고한다:
- 조건 전문
- 경과 시간(`started_at` 기준)
- 평가된 턴 수(`turns_evaluated`)
- 최근 평가 사유(`last_reason`)
- 활성 목표가 없고 직전에 달성된 것이 있으면(`status: achieved`) 달성 조건·소요를 보여준다.

### 3. 목표 해제 — `/goal clear`

`status: cleared` 로 갱신하고 루프를 중단, 제어를 사용자에게 반환한다.
별칭: `stop`, `off`, `reset`, `none`, `cancel` — 모두 clear로 처리한다.

## 동작 루프

활성 목표가 있는 동안 매 작업 단위마다:

```
- [ ] 1. var/goal/active_goal.md 읽기 — 활성 아니면 일반 동작으로 복귀
- [ ] 2. 조건을 향해 가장 작은 안전한 작업 단위 1개 수행
- [ ] 3. 명시된 검증을 실행해 증거를 대화에 surfacing (예: pytest 출력, exit code, git status)
- [ ] 4. 평가: surfaced 증거만으로 조건이 충족됐는가? (아래 평가 방식)
- [ ] 5a. 충족 → status: achieved 로 기록, 사유 적고 루프 종료·보고·제어 반환
- [ ] 5b. 미충족 → turns_evaluated += 1, last_reason 갱신, 다음 단위 계속 (제어 반환 금지)
```

핵심: 미충족이면 **턴을 끝내고 사용자에게 묻지 말고** 자율 루프 안에서 계속 작업한다.
한 턴 안에서 다수 단위를 수행하고, 턴이 끝나야 하면 상태 파일에 진행을 보존해 다음 턴이 이어받는다.

## 효과적인 조건 작성

평가기는 명령을 직접 실행하거나 파일을 읽지 않고 **에이전트가 surfacing한 출력**만 판단한다.
따라서 조건은 에이전트의 출력으로 증명 가능한 형태로 쓴다.

좋은 조건의 구성:
- **측정 가능한 단일 종료 상태** — 테스트 결과, 빌드 exit code, 파일 개수, 빈 큐
- **증명 방법 명시** — 예: `python -m pytest tests/auth exits 0`, `git status is clean`
- **불변 제약** — 도중에 바뀌면 안 되는 것, 예: `다른 테스트 파일은 수정하지 않는다`

실행 시간을 제한하려면 조건에 턴/시간 절을 포함한다(예: `or stop after 20 turns`).
매 턴 그 절 대비 진척을 보고하고 평가에 반영한다. 조건은 최대 4,000자.

예시:
```
/goal tests/auth의 모든 테스트가 통과하고 ruff check . 가 깨끗하다. 다른 테스트 파일은 수정하지 않는다. or stop after 20 turns
```

## 평가 방식

- 평가는 **이번 턴까지 대화에 드러난 증거만** 근거로 한다. 실행하지 않은 결과를 가정하지 않는다.
- 매 평가는 작업하던 관점이 아니라 신선한 시각으로 yes/no + 한 줄 사유를 산출한다.
- 더 강한 독립성이 필요하면 readonly 평가 서브에이전트(Task, 빠른 모델)에 surfaced 증거를 넘겨
  판정만 받는다. 비용이 부담되면 자기평가로 충분하다.
- `no` 의 사유는 다음 단위의 가이드로 쓴다. `yes` 면 목표를 해제하고 달성 항목으로 기록한다.

## 가드레일 (AGENTS.md 정합)

- 자율 루프라도 [AGENTS.md](../../../AGENTS.md) 권한·종료 상태를 준수한다.
- **commit·push·PR·merge·plan CLOSED 는 자동 수행 금지** — 사용자가 명시 요청해야 한다.
  목표 조건이 "PR 머지"여도 머지 직전 단계까지만 진행하고 멈춘다.
- 같은 root cause로 3회 연속 수정 실패, 도메인 규칙 충돌, 검증 명령 부재, 승인 필요한 고위험
  변경 → 루프를 중단하고 `BLOCKED:` 형식으로 보고(상태 파일은 active 유지).
- 검증은 dual gate를 따른다([shapez2-core.mdc](../../rules/shapez2-core.mdc)). `-q`/`--quiet`/`--tb=no` 금지.
- 마감 보고는 Caveman 6절(Summary·Files·Contracts·Tests·Risks·Next) 형식을 쓴다.

## 참고

- 평가 메커니즘·다른 자율 워크플로(loop·Stop hook·auto)와의 비교: [reference.md](reference.md)
- 목표 주도 자율 개발 루프 정본: [AGENTS.md](../../../AGENTS.md) §Goal-Driven Autonomous Development Loop
