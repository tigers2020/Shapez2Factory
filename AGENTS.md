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
6. 범위가 닫히고 narrow 검증이 green이면 [PR finish and closing](#pr-finish-and-closing-agent-owned)을 사용자 재요청 없이 수행한다.
7. 최종 응답에는 Caveman 6절([`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) §17)과 Output contract 형식으로 요약한다.

## PR finish and closing (agent-owned)

구현·narrow 검증이 끝나 범위가 닫혔으면, 사용자가 「PR 올려」「마무리해」「크로징」이라고 말하지 않아도 에이전트가 아래를 **끝까지** 수행한다. 마지막 턴은 PR URL·검증 결과·`CLOSED` 반영 여부를 보고한다.

### 전제 (진행 금지)

- 프로토콜 4단계(승인)가 필요한 대형 변경은 승인 전 push/PR 금지 ([`protocols/README.md`](protocols/README.md)).
- Full gate 실패, `BLOCKED:`, 고위험 변경 대기, 사용자가 WIP/draft로 남기라고 명시한 경우.

### 체크리스트 (순서 고정)

1. **Full gate** — `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .` (전부 green).
2. **Commit** — 요청 범위만 스테이징; Conventional Commits 스타일; `.env`·secrets·`var/`·`.pytest_cache`/`.ruff_cache` 등 산출물·캐시 제외.
3. **Push** — feature branch: `git push -u origin HEAD`. `main`/`master` 직접 push·`--force`·`--no-verify` 금지.
4. **PR** — `gh`로 생성 또는 기존 PR 갱신(Summary + Test plan). [`documents/ai/manuals/cursor_usage.md`](documents/ai/manuals/cursor_usage.md)의 PR 본문 형식 준수.
5. **CI** — 실패 시 원인 수정 후 재push; 반복 triage는 babysit·[`testing.md`](documents/ai/manuals/testing.md) dual gate 기준.
6. **Closing** — [`documents/ai/current_plan.md`](documents/ai/current_plan.md) 등 해당 plan 항목 `CLOSED`·날짜 반영; 관련 스펙/런타임 문서와 코드 불일치 없음 확인.

### Merge·승인

- **기본**: PR 개설·CI green·closing 문서까지가 에이전트 책임.
- **squash merge / main 병합**: 사용자 또는 리뷰어가 명시 요청한 경우에만 `gh pr merge` 등 실행.

### 사용자 확인이 필요할 때만 멈춤

- `main`/`master` force push, 대규모 `pyproject.toml`/CI·배포 설정 변경, 보안·권한 파일.
- 플랜 미승인 대형 기능, 의도적 draft PR 유지 지시.

## Validation commands

로컬 pytest 기본: `powershell -File scripts/test_fast.ps1` (상세: [`documents/ai/manuals/testing.md`](documents/ai/manuals/testing.md) § 로컬 스크립트).

Asteroid Lab Run Solver (UI 없이): `python manage.py run_solver --slug <slug>` — stack log: `var/log/solver_summary_stack/` ([`01_entry_point.md`](documents/Algorithm/solver_runtime/01_entry_point.md)).

```bash
powershell -File scripts/test_fast.ps1   # 일상 TDD
ruff check .
mypy django_apps config src
black --check .
```

PR/병합 full gate: `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .`
실패 시 억지로 완료 선언하지 않고 `BLOCKED:` 형식으로 보고한다.

### pytest 출력 규칙 (필수)

**pytest 실행 시 출력 억제 플래그 사용 금지.**

| 금지 플래그 | 이유 |
|---|---|
| `-q` / `--quiet` | 실패 상세가 숨겨져 에러를 놓침 |
| `--tb=no` | traceback 제거로 디버그 불가 |
| `--no-header` | 단독 사용 시 컨텍스트 소실 |
| `-p no:terminal` | 출력 완전 억제 |

허용: `-v`, `-s`, `--tb=short` (기본값), `--tb=long`, `-x`, `--maxfail=N`.

상세·Forbidden shortcuts: [`documents/ai/manuals/testing.md`](documents/ai/manuals/testing.md) § pytest 출력 규칙.

## Permissions

- 기본 권한: 읽기, 검색, 계획 수립
- 허용된 쓰기: workspace 내부의 소스 / 테스트 / 문서
- **PR finish and closing** 시 추가 허용(전제·체크리스트 충족 시, 별도 재요청 불필요):
  - feature branch `git commit` / `git push`
  - `gh pr create` · PR 본문 갱신 · CI 상태 확인
  - plan·`documents/ai/current_plan.md` 등 closing 메타데이터 갱신
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
  - **선행 underscore 토글 rename** — `func`↔`_func` 등 이름이 선행 `_` 추가·제거만 다른 변경(함수·메서드·변수·파라미터·동일 의미 import alias). 스타일 정리·린트 맞추기·가독성 목적으로 하지 않는다. 요청·승인 스펙·버그 수정에 **필수인 새 심볼**만 예외.

상세: [`.cursor/rules/shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) Forbidden Shortcuts · [`testing.md`](documents/ai/manuals/testing.md) § Forbidden shortcuts.

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
- narrow 검증 + (PR 대상이면) full gate 결과가 제시되었다.
- 실패한 검증이 남아 있으면 명시되었다; green이면 [PR finish and closing](#pr-finish-and-closing-agent-owned) 체크리스트 완료 또는 `BLOCKED:` 사유.
- 문서와 코드가 서로 모순되지 않는다.
- PR이 해당되면 URL·브랜치·CI 상태(또는 merge 보류 사유)가 최종 응답에 포함된다.
- 해당 plan 항목이 `CLOSED`로 반영되었거나, 크로징 불가 시 그 이유가 명시되었다.

## References

- [Persona index](persona/README.md)
- [Protocol pipeline](protocols/README.md)
- [Architecture rules](.cursor/rules/architecture.mdc)
- [Cursor memo](documents/CURSOR_MEMO.md)
