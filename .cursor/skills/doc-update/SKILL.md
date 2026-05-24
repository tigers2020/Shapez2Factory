---
name: doc-update
description: 코드 변경 후 문서, 계획, ADR, runbook을 동기화할 때 사용한다.
paths:
  - "docs/**"
  - "AGENTS.md"
  - ".cursor/rules/**"
  - "persona/**"
  - "protocols/**"
disable-model-invocation: true
metadata:
  owner: "project"
  risk: "low"
  requires_validation: false
---

# Doc Update

## Intent

코드와 문서가 서로 모순되지 않도록 유지한다. "문서가 진실"이므로 코드 변경 시 문서를 후행 동기화한다.

## Inputs

- 최근 변경 파일 목록
- 변경 의도 또는 plan 파일
- 영향받는 docs 경로 (있는 경우)

## Procedure

1. 최근 변경 파일과 plan을 읽는다.
2. 영향받는 docs 영역을 찾는다:
   - 동작 변경 → `docs/domain/README.md` 또는 관련 도메인 문서
   - 아키텍처 변경 → `docs/architecture/README.md`
   - 반복 절차 변경 → `docs/runbooks/`
   - 설계 결정 → `docs/adr/`에 ADR 추가
3. 코드와 문서가 충돌하는 문장을 우선 수정한다.
4. 필요한 경우 ADR 또는 runbook을 추가한다 (`docs/adr/ADR-0000-template.md` 참조).
5. 더 이상 유효하지 않은 예시는 제거한다.
6. 저장소 경로·앱·테스트 트리 변경 시 [`structure.md`](../../../structure.md) (Repository map SoT)를 먼저 갱신한다.
7. `AGENTS.md`의 **Repository routing**(SoT 링크·work-type 표)과 Definition of done이 여전히 유효한지 확인한다. AGENTS에 전체 path 표를 중복 추가하지 않는다.

## Output

```
Summary:
Files changed:
Commands run:
Validation: (N/A - doc only)
Risks / follow-up:
Docs updated:
```

## Failure handling

- 변경 의도가 불명확하면 `BLOCKED: missing context` 후 plan 확인 요청
- 코드-문서 충돌 해소 불가 시 사용자 판단 요청

## References

- `@docs/adr/ADR-0000-template.md`
- `@docs/runbooks/bugfix-runbook.md`
- `@AGENTS.md`
