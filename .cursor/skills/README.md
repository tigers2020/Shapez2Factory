# Skills Index

이 디렉터리는 Cursor가 자동 발견하는 프로젝트 수준 스킬 저장소다.

## 활성 스킬 (phase1)

| 스킬 | 경로 | 목적 |
|---|---|---|
| bug-fix | `bug-fix/SKILL.md` | 실패 로그/재현 절차 기반 최소 수정 + 회귀 테스트 추가 |
| write-tests | `write-tests/SKILL.md` | 구현 전/후 테스트 작성·보강 |
| doc-update | `doc-update/SKILL.md` | 코드 변경 후 문서·ADR·runbook 동기화 |

## 비활성 스킬 (phase3 이후 활성화)

아래 스킬은 `tests/golden/`에 결정적 회귀 검증 데이터셋이 갖춰진 뒤에 추가한다.

| 스킬 | 게이트 조건 |
|---|---|
| feature-add | golden test 또는 acceptance criteria 기반 테스트 최소 1개 이상 |
| refactor | characterization test 또는 golden diff 확보 |

## 스킬 추가 절차

1. `research.md` 또는 `docs/domain/`에 근거 문서를 먼저 작성한다.
2. `SKILL.md` 초안을 작성하고 시몬이 승인한다.
3. `references/`, `scripts/`는 스킬이 실제로 사용될 때 추가한다.
4. 스킬 본문은 짧게 유지하고 세부 내용은 `references/`로 분리한다.
