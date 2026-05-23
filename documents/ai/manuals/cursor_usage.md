# 매뉴얼: Cursor 사용 습관 · 컨텍스트 · 에이전트 네이티브 엔지니어링

이 문서는 **에이전트가 매 턴 읽는 규칙을 늘리지 않기 위해** `documents/ai/manuals/`에 둔 온디맨드 참고용이다. 상시 규칙 정본은 [`AGENTS.md`](../../../AGENTS.md)와 [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc)이다.

루트 [`AGENTS.md`](../../../AGENTS.md)의 **에이전트 네이티브 엔지니어링(요약)** 과 아래 본문이 같은 철학을 공유한다.

## 1. 왜 토큰·한도가 빨리 닳는가

- 채팅/컴포저에서 **한 번 보낼 때마다**, 대화 이력·첨부·일부 시스템·규칙이 **입력 컨텍스트로 함께** 실린다. 스레드가 길수록 같은 질문이라도 **입력량이 커진다**.
- 주제가 다른 작업의 로그·에러·코드 덩어리가 한 스레드에 남아 있으면 **노이즈와 비용이 동시에** 늘어난다. 품질이 떨어지면 수정 반복으로 **출력 토큰**도 증가할 수 있다.

구체적인 **플랜 한도·모델별 단가·배수**는 시점별로 변하므로 Cursor 앱의 **설정·Billing / Usage**와 공식 안내를 본다.

## 2. 하네스 관점 (Human ↔ Agent ↔ Harness)

에이전트는 프롬프트·규칙, 코드 검색, 터미널, 모델의 조합으로 동작한다. 이 레포에서는 [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc)·[`AGENTS.md`](../../../AGENTS.md)·[`protocols/README.md`](../../../protocols/README.md)·스킬([`.cursor/skills/shapez2-harness/SKILL.md`](../../../.cursor/skills/shapez2-harness/SKILL.md), [`.cursor/skills/cursor-shapez2-harness/SKILL.md`](../../../.cursor/skills/cursor-shapez2-harness/SKILL.md))이 **하네스**에 해당한다.

## 3. 의도 정밀도와 프롬프트

- **나쁜 예**: 한 줄 요청만으로 넓은 탐색·추측 구현을 유도한다.
- **좋은 예**: 기존 패턴을 가리키는 경로·심볼, 로그나 재현 단계, 원하는 구조, 금지 사항(솔버 동작 변경 금지, `func`↔`_func` 같은 underscore 토글 rename 금지 등), 완료 조건(실행할 `pytest` 경로 등)을 명시한다.

의도 정밀도가 오르면 환각·무관 탐색이 줄고, 아키텍처 일관성을 지키기 쉽다.

## 4. 컨텍스트를 “작업 기억”으로 쓰기

- 대형 기능·난해한 버그는 **새 스레드**로 시작하는 것을 권장한다.
- 동작이 이상해지면 **세션을 갈아엎는** 편이 나을 수 있다.
- 레포가 크면 토큰이 급증하고 추론 품질이 떨어질 수 있으므로, **참조 범위는 최소**로 한다 (`@` 파일·폴더는 필요한 것만).

## 5. 코드 탐색 전략

| 유형 | 수단 | 쓰임 |
|------|------|------|
| **Literal** | `grep`/ripgrep, 심볼 검색 | 정확한 함수명·문자열·에러 메시지 |
| **Semantic** | “인증은 어디서?” 같은 질의, 시맨틱 검색, Serena 등 | 흐름·미들웨어·간접 호출 |

둘을 섞어 쓰고, **이해가 선행**된 뒤에 수정 범위를 좁힌다.

## 6. 서브에이전트·작업 격리

광역 탐색·영향 범위 조사는 **별도 컨텍스트**(서브에이전트·백그라운드 태스크 등)에서 돌리고, **결과만** 본 스레드로 가져오면 본문 컨텍스트 오염을 줄일 수 있다. Pass·Recovery·Replay·검증처럼 주제가 다른 일은 분리하는 것이 좋다.

## 7. “이해하기 전에 수정하지 말 것”

에이전트는 기존 유틸을 모르고 중복을 만들거나, 레이어·패턴을 무시하거나, **아키텍처 드리프트**를 일으킬 수 있다.

이 레포의 채굴·배치 솔버는 replay·recovery·routing·protected corridor·reclaim·Pass 등이 **서로 얽혀** 있으므로, 호출 관계와 `documents/` 정본을 확인하지 않은 수정은 위험하다. 프로젝트 규칙: 의미 있는 변경은 **리서치·플랜·승인 게이트**를 따른다 ([`AGENTS.md`](../../../AGENTS.md), [`protocols/README.md`](../../../protocols/README.md)).

## 8. 기능 개발 흐름 (권장)

1. 계획(질문 정리·범위)
2. 명확화 질문
3. **스스로 검증 가능한 단계**로 분해한 실행 계획
4. 구현
5. 검증 — **Contract-first TDD**([`testing.md`](testing.md)): 반복 narrow `pytest` → PR full gate(`ruff` → `black --check` → `mypy` → 전체 `pytest`). **`-q` / `--quiet` / `--tb=no` 금지** (실패 상세 누락).
6. 반복

큰 기능을 한 번에 구현하지 말고, 단계마다 통과 조건을 두는 것이 안전하다.

## 9. 디버깅 원칙

1. **재현** 가능해야 한다.
2. **최소 케이스**로 축소한다.
3. **변경 범위**를 격리한다.
4. **근본 원인 가설**을 세운 뒤 증거로 검증한다.
5. 필요 시 **로그·계측**을 추가한다.
6. **회귀 테스트**를 남긴다.

“에러 고쳐줘” 한 줄보다, 런타임 증거·가설·재현을 함께 주는 편이 효율적이다.

## 10. 멀티 모델·교차 검증

동일 버그를 **서로 다른 모델·에이전트**에 병렬로 맡기면 접근이 달라질 수 있다. 다만 **설명이 곧 정답은 아니다**: 근본 원인, 엣지 케이스, 타입 안전성 등은 사람·테스트·로그로 **반드시 검증**한다.

## 11. 코드 리뷰·커밋

- AI가 쓴 코드도 **인간 리뷰 기준**과 동일하게 본다.
- 큰 diff는 **의미 단위 커밋**으로 쪼개면 리뷰어 이해도가 오른다.

## 12. 테스트와 CI 비용

에이전트 시대에는 테스트·린트·타입체크를 **짧은 주기로 많이** 돌리게 되므로, **느린 스위트·전체 pytest 남발**이 비용과 대기 시간을 키운다. **기본은 이번에 수정한 코드에 대응하는 테스트 파일·디렉터리만** 실행하고, 마커·경로로 좁힌다 ([`testing.md`](testing.md) 상단, [`AGENTS.md`](../../../AGENTS.md) 테스트 표). 루트에서 `python -m pytest` 전체는 **꼭 필요할 때만**. 출력 억제(`-q`, `--quiet`, `--tb=no`)는 **금지** — [`testing.md` § pytest 출력 규칙](testing.md).

회귀 방지를 위해 기능·버그 수정마다 **가능한 한 테스트**를 남기는 것을 권장한다.

## 13. Rules vs Skills

| 구분 | 역할 | 이 레포 예 |
|------|------|------------|
| **Rules** | 상시 적용되는 짧은 지시 | `shapez2-core.mdc` + `AGENTS.md` (glob 규칙은 작업 경로에만) |
| **Skills** | 필요할 때만 여는 절차 묶음 | `/merge-all`, `shapez2-harness`, `cursor-shapez2-harness`, `data-pipeline-harness`, `code-review-harness`, `research-harness` 스킬, 이 매뉴얼을 `@`로 참조 |

규칙 파일에 긴 본문을 중복 넣지 말고, 매뉴얼·플랜에 두고 링크한다.

## 14. 이 레포와의 관계 (실무 습관 표)

| 습관 | 설명 |
|------|------|
| 작업 단위로 스레드 분리 | 한 작업이 끝나거나 주제가 바뀌면 **새 채팅**으로 시작한다. (`/clear`에 해당하는 “방 비우기”와 같은 목적.) |
| 모델 선택 | 기본은 상대적으로 부담이 적은 모델에 두고, **설계·난해한 디버깅** 등 필요할 때만 더 무거운 모델로 바꾼다. |
| 참조 범위 최소화 | `@파일`·`@폴더`는 **정말 필요한 경로만**. 넓은 폴더·코드베이스 전체 탐색 요청은 도구 호출·검색 결과로 컨텍스트가 불어난다. |
| 프롬프트 구체화 | 파일 경로·심볼 이름·완료 조건(테스트 명령 등)을 적어 **불필요한 탐색**을 줄인다. |

- [`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc)·[`AGENTS.md`](../../../AGENTS.md)만 **매 턴** 실린다. 같은 내용을 규칙에 중복 넣지 말고 **매뉴얼·플랜**에 두고 `@`로 연다.
- MCP는 온디맨드. 미사용 MCP 서버는 끄면 부담 감소 (Cursor slim 가이드: [`cursor_slim_setup.md`](cursor_slim_setup.md)).
- 구조·심볼 추적은 **Serena** + `@mcp` (`initial_instructions` 선행).

## 15. Transcript 철학과 프로젝트 정렬 (요약)

| 아이디어 | 이 레포에서의 대응 |
|----------|-------------------|
| Plan-first | `documents/` 플랜·승인, [`checklist.md`](../checklist.md) |
| 컨텍스트 분리 | 스레드·서브에이전트·phase 문서 |
| 계측·리플레이 | computation_cycle, 이벤트·리커버리 트레이스 등(해당 모듈 정본 따름) |
| 검증 게이트 | [`testing.md`](testing.md) dual gate: 반복 narrow `pytest` / PR `ruff`→`black --check`→`mypy`→`pytest` |
| 추상화 경계 | recovery·replay·routing·corridor 등 **중복 추상화 감시** ([`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) 단순성) |

## 16. 관련 매뉴얼

- 범위 큰 변경: [`documents/ai/`](../../README.md)의 플랜·체크리스트
- 테스트 구간: [`testing.md`](testing.md)

## Cloud VM

Cursor Cloud / 원격 VM에서만 적용한다.

- **서비스**: Django dev server만. Docker·Redis·Celery·외부 DB 불필요.
- **DB**: SQLite 기본. 최초 `python3 manage.py migrate`로 `db.sqlite3` 생성(멱등).
- **서버**: `python3 manage.py runserver 0.0.0.0:8000` (`python`은 PATH에 없을 수 있음).
- **PATH**: `export PATH="/home/ubuntu/.local/bin:$PATH"` (`black`, `ruff`, `mypy`, `pytest`).
- **Solver API** (`POST /api/solver/solve/`): CSRF — 페이지에서 `csrftoken` 쿠키 후 `X-CSRFToken` + cookie.
- **프론트**: CSS/JS 번들 커밋됨. `assets/css/`, `frontend/` 수정 시만 `npm install` / `npm run build`.
- **그래프 프리뷰**: 기본 `playwright_png`. Playwright 없이 돌릴 때는 `.env.debug`에 `SOLVER_GRAPH_PREVIEW_RENDERER=noop` (`.env.debug.example` 참고, [`environment.md`](environment.md)).
- **검증 명령**: [`testing.md`](testing.md) 표. `black --check .`는 `django_apps/web/views/macro_staff.py`에 기존 포맷 이슈 1건 있을 수 있음.

## 17. Caveman 출력 (필수)

**목적**: 채팅·마감 보고 **출력 토큰** 절감(실무 15–40% 목표; 과장 금지). **내부 추론·게이트 품질은 유지**, narration만 압축.

### 3계층 (교차 참조)

| 계층 | 정본 |
|------|------|
| 라우팅 | [`AGENTS.md`](../../../AGENTS.md) |
| Rule (alwaysApply) | [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) · glob [`asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc) |
| 매뉴얼 | 본 절 · [`testing.md`](testing.md) · [`checklist.md`](../checklist.md) |

레포 작업 시 장문 prose보다 **AGENTS + shapez2-core** 우선.

### MUST — 6절 (순서·제목 변경 금지)

```text
## Summary
## Files
## Contracts
## Tests
## Risks
## Next
```

| 절 | 내용 |
|----|------|
| Summary | 1–3 bullets; 구현 3단계는 `[시몬]`·`[담당]` bullet 후 코드 |
| Files | `path — why` |
| Contracts | 불변식·DTO·스키마 |
| Tests | `cmd — pass\|fail\|skipped — note` |
| Risks | 회귀·`uncertain:`·`assumption:` |
| Next | 이후 진행; 끝났을 때만 「완료」 |

**6절 없이 마감 = 미완료** ([`checklist.md`](../checklist.md)).

### 예외 (6절 생략)

1. Plan mode 플랜 본문 (구현 후 채팅은 6절)
2. 사용자 「상세 설명·교육·리뷰」 명시
3. `documents/` **파일 본문** 작성·수정 (한국어 정본)

### 온디맨드

긴 replay/DTO 세션: [`.cursor/skills/caveman-mode/SKILL.md`](../../../.cursor/skills/caveman-mode/SKILL.md) (`@caveman-mode`).
