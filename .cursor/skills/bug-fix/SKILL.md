---
name: bug-fix
description: >-
  Bug fix or contract tests: repro from failure log, minimal fix, regression/acceptance
  tests, validation gate. Use for /bug-fix, failing tests, or test-only PR scope.
paths:
  - "django_apps/**"
  - "src/**"
  - "tests/**"
disable-model-invocation: false
metadata:
  owner: project
  risk: medium
  requires_validation: true
---

# Bug Fix & Tests

## Intent

재현 가능한 버그는 최소 diff로 고치고, 스펙/불변식은 테스트로 고정한다.

## Modes

| Mode | When | Production edits |
|------|------|------------------|
| **Fix** | Failure log or repro steps | Yes — smallest safe diff |
| **Tests only** | Spec/acceptance exists; tests missing | No — tests only unless user expands |

## Procedure (fix)

1. Root cause 가설 1~2개로 줄인다.
2. 관련 소스·테스트를 찾는다.
3. 재현 테스트 없으면 먼저 작성(RED).
4. 최소 수정(GREEN).
5. 동일 유형 회귀 테스트 1개 이상 추가.
6. 검증: narrow `pytest <path>` → `ruff check .` → `mypy django_apps config src` → `black --check .` (no `-q`/`--quiet`/`--tb=no` — [`testing.md`](../../../documents/ai/manuals/testing.md)).

## Procedure (tests only)

1. 기대 입출력 또는 invariant를 명문화한다.
2. Acceptance test 먼저 — 구현 전 실패 확인.
3. Mock은 외부 경계(DB/FS/API)만.
4. 레이어 선택: `tests/unit/` · port-fake unit · `tests/integration/` · `tests/golden/` (가장 저렴한 것).
5. narrow `pytest` → 필요 시 `scripts/test_fast.ps1`.

## Output

```text
Summary:
Files changed:
Commands run:
Validation:
Risks / follow-up:
```

## Failure handling

- 재현/스펙 불명 → `BLOCKED: missing context`
- 리스크 높음 → 사용자 승인 전 중단

## References

- [`AGENTS.md`](../../../AGENTS.md) § Validation
- [`tests/golden/README.md`](../../../tests/golden/README.md)
