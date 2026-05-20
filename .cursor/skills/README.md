# Skills Index

Cursor가 자동 발견하는 프로젝트 수준 스킬 저장소.

## 활성 스킬

### 자동 호출 (`disable-model-invocation: false`)

| 스킬 | 경로 | 목적 |
|---|---|---|
| bug-fix | `bug-fix/SKILL.md` | 실패 로그·재현 절차 기반 최소 수정 + 회귀 테스트 추가 |
| write-tests | `write-tests/SKILL.md` | 구현 전/후 테스트 작성·보강 |
| doc-update | `doc-update/SKILL.md` | 코드 변경 후 문서·ADR·runbook 동기화 |

### 수동 호출 전용 (`disable-model-invocation: true`)

`@스킬명` 또는 `/스킬명`으로 명시 호출할 때만 사용한다.

| 스킬 | 경로 | 목적 |
|---|---|---|
| shapez2-workflow | `shapez2-workflow/SKILL.md` | 10단계 파이프라인 + Cursor IDE 절차 + dual gate 통합 오케스트레이션 |
| git-workflow | `git-workflow/SKILL.md` | 안전한 git 스테이징·커밋·push |

## 비활성 / 아카이브

`_archive/` — 참고용으로 보관, 자동 호출되지 않음.

유틸 명령 모음: [`documents/ai/runbooks/dev_commands.md`](../../documents/ai/runbooks/dev_commands.md)

## 스킬 추가 절차

1. `documents/ai/` 근거 문서를 먼저 작성한다.
2. `SKILL.md` 초안을 작성하고 시몬이 승인한다.
3. 이 README 표에 추가한다.
