# AGENTS.md

## Mission

이 저장소의 목표는 `shapez2 Factory Planner` 이다.
당신은 항상 **작은 안전한 변경 + 빠른 검증 + 문서 동기화** 원칙으로 행동한다.

## Trigger

다음 중 하나가 보이면 이 문서를 최우선 운영 계약으로 사용한다.

- 새 기능 요청
- 버그 리포트
- 테스트 실패
- 리팩터 요청
- 성능/안정성 개선 요청

## Repository map

| 경로 | 목적 |
|---|---|
| `src/shapez2_factory/domain/` | 순수 비즈니스 규칙, 값 객체, 정책 (도미닉) |
| `src/shapez2_factory/application/` | use case, DTO, port 추상화 (유리) |
| `src/shapez2_factory/adapters/` | 외부 시스템 구현, 응답→DTO 변환 (아다) |
| `src/shapez2_factory/interfaces/` | UI 화면, 사용자 상태, 위젯 조합 (지나) |
| `src/shapez2_factory/bootstrap/` | 조립, dependency wiring (시몬) |
| `django_apps/` | Django-first 런타임 앱 (데니) |
| `config/` | Django 설정·루트 URL (데니) |
| `tests/` | unit / integration / golden (테스) |
| `docs/domain/` | 도메인 매뉴얼 — 도메인 용어, 불변식 |
| `docs/architecture/` | 시스템 구조·모듈 책임·데이터 흐름 |
| `docs/runbooks/` | 반복 개발 절차 실행 가이드 |
| `docs/adr/` | 아키텍처 결정 기록 |
| `.cursor/rules/` | 경로별 기계 친화 규칙 |
| `.cursor/skills/` | 반복 작업 스킬 패키지 |
| `persona/` | 팀 페르소나 카드 |
| `protocols/` | 거시 10단계 파이프라인 정본 |
| `documents/` | 메모, 플랜, 리서치 문서 |
| `harness/validators/` | 검증 스크립트·golden comparator (phase2) |
| `tests/golden/` | 결정적 회귀 검증 데이터셋 (phase2) |

참조: `@docs/domain/`, `@docs/architecture/`, `@docs/runbooks/`, `@.cursor/rules/`, `@.cursor/skills/`

## Manual routing

작업 유형 하나를 고른 뒤 **해당 페르소나·매뉴얼만** 연다 ([`documents/ai/manuals/`](documents/ai/manuals/)).

| Work type | Persona | Must read |
|-----------|---------|-----------|
| `django` | [데니](persona/denny.md) | [`documents/ai/manuals/django.md`](documents/ai/manuals/django.md); models/migrations 시 [`database.md`](documents/ai/manuals/database.md) |
| `database` | 데니 | `database.md` + `django.md` |
| `solver` | 도미닉·유리 | [`solver.md`](documents/ai/manuals/solver.md) |
| `frontend` / `graph UI` | 지나 | web/frontend 관련 매뉴얼 |
| `tests` | 테스 | [`testing.md`](documents/ai/manuals/testing.md) |
| `asteroid_lab` | 데니 + 불변식 | [`asteroid-lab-invariants.mdc`](.cursor/rules/asteroid-lab-invariants.mdc) |

`django_apps/**`·`config/**` 변경은 **데니** 소유. hexagonal `src/shapez2_factory/` 만 도미닉·유리·아다·지나.

## Required workflow

1. 관련 `docs/domain/`, `docs/architecture/`, `AGENTS.md`와 코드를 읽고 문제를 재정의한다.
2. Plan Mode 스타일로 변경 대상 파일, 리스크, 검증 방법을 정리한다.
3. 구현은 가장 작은 단위로 수행한다.
4. 변경 후 반드시 아래 검증 4단계를 실행한다.
5. 동작/설계가 바뀌면 `docs/` 와 plan 을 갱신한다.
6. 최종 응답에는 Output contract 형식으로 요약한다.

## Validation commands

```bash
pytest -q
ruff check .
mypy django_apps config src
black --check .
```

순서: `pytest` → `ruff check .` → `mypy django_apps config src` → `black --check .`
실패 시 억지로 완료 선언하지 않고 `BLOCKED:` 형식으로 보고한다.

## Permissions

- 기본 권한: 읽기, 검색, 계획 수립
- 허용된 쓰기: workspace 내부의 소스 / 테스트 / 문서
- 사용자 승인 필요:
  - 환경설정 파일 (`.env`, `pyproject.toml` 대형 변경)
  - CI/배포 설정
  - 보안/권한 관련 파일
  - 대규모 rename / delete
- 금지:
  - secrets 읽기 시도
  - `.env`, credential, token 파일 노출
  - 생성 산출물 직접 수정
  - 검증 없이 완료 선언

## Tools

- 코드 탐색/검색: 적극 사용
- 터미널: 검증과 재현에만 사용, destructive command 금지
- 브라우저: UI/시각 검증 필요 시 사용
- MCP: 프로젝트에 설정된 것만 사용 (`.cursor/mcp.json` 참조)
- 스킬: 관련 스킬이 있으면 `@.cursor/skills/` 우선 호출

## Input contract

입력은 다음 중 하나여야 한다.

- 이슈/티켓 설명
- 실패 로그
- 원하는 동작의 예
- 기준 파일/스펙 문서

정보가 부족하면 구현 전에 부족한 입력을 명시한다.

## Output contract

항상 아래 형식으로 마무리한다.

```
Summary:
Files changed:
Commands run:
Validation:
Risks / follow-up:
Docs updated:
```

## Failure handling

아래 상황이면 억지로 진행하지 말고 중단한다.

- 도메인 규칙이 서로 충돌
- 검증 명령을 찾지 못함
- 회귀 가능성이 큰데 기준 테스트가 없음
- 사용자 승인 없는 고위험 변경 필요

중단 형식:

```
BLOCKED:
- missing context:
- risky change:
- recommended next step:
```

## Security and privacy

- `.cursorignore` 대상은 읽지 않는다.
- 민감값은 절대 요약/출력하지 않는다.
- 외부 전송이 필요한 도구는 최소 권한만 사용한다.
- terminal / MCP auto-run 은 명시된 allowlist 밖에서 가정하지 않는다.

## Definition of done

- 요청 범위를 벗어나지 않았다.
- 테스트/빌드/검증 결과가 제시되었다.
- 실패한 검증이 남아 있으면 명시되었다.
- 문서와 코드가 서로 모순되지 않는다.

## References

- [Persona index](persona/README.md)
- [Protocol pipeline](protocols/README.md)
- [Architecture rules](.cursor/rules/architecture.mdc)
- [Cursor memo](documents/CURSOR_MEMO.md)
