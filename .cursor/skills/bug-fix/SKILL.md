---
name: bug-fix
description: 실패 로그나 재현 절차가 주어졌을 때 최소 수정으로 원인을 제거하고 회귀 테스트를 추가한다.
paths:
  - "src/**"
  - "tests/**"
  - "docs/**"
disable-model-invocation: false
metadata:
  owner: "project"
  risk: "medium"
  requires_validation: true
---

# Bug Fix

## Intent

재현 가능한 버그를 최소 diff로 수정하고, 동일 유형 회귀를 막는 테스트를 추가한다.

## Inputs

- 실패 로그 또는 재현 절차
- 기대 동작 설명
- 관련 테스트 파일 (있는 경우)

## Procedure

1. 로그/재현 절차를 읽고 root cause 가설을 1~2개로 줄인다.
2. 관련 소스(`src/`)와 테스트(`tests/`)를 찾는다.
3. 수정 전 spec-linked 재현(acceptance) 테스트가 없으면 최소 재현 테스트를 먼저 작성한다.
4. 수정은 smallest diff 원칙으로 수행한다.
5. 동일 종류 회귀를 막는 테스트 한 개 이상을 추가한다.
6. 검증 체인을 실행한다: narrow `python -m pytest <path>` → `ruff check .` → `mypy django_apps config src` → `black --check .` (`-q` / `--quiet` / `--tb=no` 금지 — [`testing.md`](../../../documents/ai/manuals/testing.md)).
7. 변경 원인과 검증 결과를 Output 형식으로 요약한다.

## Output

```
Summary:
Files changed:
Commands run:
Validation:
Risks / follow-up:
Docs updated:
```

## Failure handling

- 재현 불가면 `BLOCKED: missing context`
- 검증 명령 미발견 시 `docs/runbooks/bugfix-runbook.md` 참조
- 리스크가 높으면 사용자 승인 전 구현 중단

## References

- `@docs/runbooks/bugfix-runbook.md`
- `@docs/domain/README.md`
- `@AGENTS.md`
