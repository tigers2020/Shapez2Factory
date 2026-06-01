---
name: write-tests
description: 구현 전/후에 테스트를 작성하거나 회귀 테스트를 보강할 때 사용한다.
paths:
  - "tests/**"
  - "src/**"
disable-model-invocation: false
metadata:
  owner: "project"
  risk: "low"
  requires_validation: true
---

# Write Tests

## Intent

기대 입출력 또는 불변식을 테스트로 명문화하여, 구현 변경 시 회귀를 조기에 발견한다.

## Inputs

- 기대 입출력 또는 invariant 설명
- 구현 파일 경로
- 실패 로그 (보강 작업인 경우)

## Procedure

1. 기대 입출력 또는 invariant를 명문화한다.
2. spec acceptance에 맞는 acceptance test를 먼저 작성하고, 구현 전 기대대로 실패하는지 확인한다.
3. mock은 꼭 필요한 경계(외부 API, DB, FS)에서만 사용한다.
4. golden / snapshot / integration 중 가장 유지비가 낮은 방식을 고른다:
   - 단순 함수: `tests/unit/`
   - use case 흐름: port fake 사용 unit test
   - 외부 의존: `tests/integration/`
   - 결정적 회귀: `tests/golden/`
5. 테스트가 통과하면 narrow `pytest` → 필요 시 `powershell -File scripts/test_fast.ps1` 또는 full gate (`-q` / `--quiet` / `--tb=no` 금지 — [`testing.md`](../../../documents/ai/manuals/testing.md)).
6. flaky 가능성이 있으면 원인과 완화책을 주석으로 기록한다.

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
- 의존 경계가 불명확하면 `docs/architecture/README.md` 확인 후 진행

## References

- `@docs/architecture/README.md`
- `@tests/golden/README.md`
- `@AGENTS.md`
