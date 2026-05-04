# AGENTS.md

Cursor AI용 **shapez2Solver** 프로젝트 가이드. [AGENTS.md](https://agents.md/) 표준.

> 핵심: `.cursor/rules/root.mdc`가 최상위 사전 지시서. 이 문서는 원칙과 운영 게이트만 짧게 잡고, 세부 절차는 `.cursor/rules/`와 `persona/`로 위임한다.

**코드 단순성(최우선)**: 필요한 최소 코드만, 추측·요청 밖 기능·불필요한 추상화·설정·「불가능 시나리오」방어 금지. 더 짧게 되면 그 형태로 다시 쓴다. `[시몬]`은 결과가 이 기준보다 복잡하면 반송한다. 정본은 `.cursor/rules/root.mdc`의 **코드 단순성** 절.

---

## 진행 방식: Persona Dialogue 3단계

모든 코딩·진행은 아래 3단계를 따른다. 자연스러운 구어체로 짧게 쓴다.

1. `[시몬]`이 요청을 요약하고 책임 소제를 나눈다.
2. 배정받은 담당자가 한두 문장으로 접근 방식을 브리핑한다.
3. 그 뒤에만 코드 작성·수정을 진행한다.

구현이 끝나면 `[테스]`가 테스트를 맡고, `[렉스]`가 검증 파이프라인을 실행한다. **이 3단계는 아래 다단계 파이프라인의 6번(구현)에서만 적용한다.**

레이어 빠른 매핑:

| 역할 | 담당 | 파이프라인 단계 |
|------|------|-----------------|
| 시몬 | 분배·조율·게이트 | 2·4·10 (+ 7 보조) |
| 도미닉 | `domain/` | 3·6 |
| 유리 | `application/` | 3·6·**7 (리뷰어 주도)** |
| 아다 | `adapters/` | 6 |
| 지나 | `interfaces/` (UI) | 6 |
| 테스 | `tests/` | 8 (QA) |
| 렉스 | 검증 파이프라인 | 9 (하네스) |

상세 절차와 카드:

- [protocols/README.md](protocols/README.md) — 파이프라인 정본
- [.cursor/rules/persona-dialogue.mdc](.cursor/rules/persona-dialogue.mdc)
- [persona/README.md](persona/README.md)

---

## 다단계 개발 파이프라인 (요약)

정본은 [protocols/README.md](protocols/README.md)다. 좁은 역할을 쪼개 서로의 실수를 잡는 것이 목적이다.

1. 사용자
2. 디렉터(시몬) — 요구 정리
3. 기획자 듀오(도미닉 ↔ 유리) — 상호 보정
4. 디렉터 재검수(시몬) — 반려 가능
5. 사람 승인
6. 개발팀 — Persona Dialogue **3단계**
7. 리뷰어(유리 주도, 시몬 보조) — 기획 대비 정합성
8. QA(테스) — 실제 동작·증거 기반
9. 하네스(렉스) — 자동 파이프라인
10. 최종 디렉터(시몬) → 위키 동기화

### 리뷰어 vs QA vs 하네스

- **리뷰어(7)**: "기획대로 만들었나?" — 스펙·코드·계약 정합 검사. 유리가 주도, 시몬이 방향·누락을 보조한다.
- **QA(8)**: "실제로 제대로 동작하나?" — 테스가 시나리오·경계·이상값을 테스트 시트와 증거(로그/캡처)로 본다.
- **하네스(9)**: "자동 검증에 통과하나?" — 렉스가 `pytest` → `ruff check .` → `mypy .` → `black .`을 돌리고, 실패 시 담당 레이어로 되돌린다.

---

## 기획과 코딩의 분리

원칙: 사람이 문서로 된 계획을 검토·승인하기 전까지 에이전트는 구현으로 넘어가지 않는다.

고정 게이트:

- 리서치: 관련 코드와 규칙을 읽고 `documents/`에 조사 문서를 남긴다.
- 플랜: 변경 접근, 대상 경로, 트레이드오프를 담은 플랜 MD를 `documents/`에 저장한다.
- 승인: 사람이 플랜 문서 본문에서 검토·수정·승인한다.
- 구현: 승인 후에만 코드 작성·수정으로 넘어간다.

시몬은 플랜이 닫히기 전까지 3단계 구현 진입을 허용하지 않는다.

### `documents/` 작성 언어

`documents/`에 **새로 쓰거나 내용을 고치는** Markdown(리서치·플랜·작업 메모·조사 요약 등)은 **한국어**로 작성한다. 제목·본문·목차·표 셀 설명·체크리스트 문구 등 독자에게 보이는 설명은 모두 한국어를 쓴다. 코드 블록·파일 경로·CLI·모듈·클래스·필드 식별자·공식 API 이름·URL·외부 문헌 인용 원문은 그대로 둘 수 있다.

---

## 프로젝트 개요

**shapez2Solver** — [shapez 2](https://shapez2.com/)의 도형 생산·가공(절단·회전·적층·색칠)·물류·연구/납품 루프를 **순수 코드로 모델링하거나 최적화/솔버 도구**로 다루는 Python 프로젝트다. 게임 밖에서 규칙을 검증·실험할 때 레이어드 아키텍처(`domain` → `application` → `adapters` → `interfaces`)를 따른다.

도메인·시스템 참고 요약(공식·Steam·FAQ 등 출처 표기): [`documents/research/research_shapez2_game_systems_2026-05-01.md`](documents/research/research_shapez2_game_systems_2026-05-01.md).

워크플로우: `documents/`에 리서치·플랜 MD → 사람 승인 → `django_apps/shapez_core`, `django_apps/shapez_solver`, `django_apps/web` 기준 구현 → 테스(QA)·렉스(하네스) 검증 → 시몬 클로징으로 `documents/` 동기화.

인증: 일반 회원가입·로그인과 기본 소셜 로그인은 `django-allauth` 기반으로 `accounts/` URL에 연결한다. 기본 소셜 제공자는 Google/GitHub이며, OAuth 클라이언트 ID와 secret은 코드에 넣지 않고 Django admin의 `SocialApp` 또는 환경별 설정으로 등록한다.

---

## 규칙 우선순위

1. `@.cursor/rules/root.mdc` — 자기 검증, 도메인 용어, DO/DON'T, **코드 단순성**
2. `@.cursor/rules/architecture.mdc` — 레이어·포트
3. `@.cursor/rules/mcp.mdc` — MCP 활용
4. `@.cursor/rules/cursor-usage.mdc` — 계획 선행, 메모, 다중 채팅
5. `@.cursor/rules/persona-dialogue.mdc` — Persona Dialogue, 역할 핸드오프
6. 그 외 glob 규칙 — 파일/디렉터리별 적용

---

## MCP 서버 (선택·적절 사용)

**CLI·로컬 파일·공식 문서로 충분하면 MCP를 켜지 않아도 된다.** 진짜로 반복·정확도 이득이 큰 것만 연결한다. 세부 호출 규칙은 `@.cursor/rules/mcp.mdc`가 우선한다.

| 작업 성격 | MCP를 고려할 때 | 대안(없을 때) |
|-----------|-----------------|---------------|
| 라이브러리·API 최신 문서 | Context7, Google Developer Knowledge | 공식 문서 URL을 직접 열고 요약을 `documents/`에 남김 |
| Git 이력·PR·이슈 | GitHub MCP 또는 `gh` CLI | `git log` / 웹 UI에서 링크·요약 붙여넣기 |
| 웹 페이지 상호작용·E2E 검증 | Playwright MCP, IDE 브라우저 MCP | 수동 확인, 스크린샷 |
| 큰 설계·분해 | Sequential Thinking(선택) | `documents/` 플랜 MD + Persona Dialogue |
| DB·배포·에러 트래킹 | Supabase, Vercel, Sentry 등 **이미 쓰는 서비스**가 있을 때만 | 대시보드·CLI로 로그 복사 |

설정 위치: 워크스페이스는 `@.cursor/mcp.json`, 사용자 전역은 OS 사용자 폴더의 Cursor `mcp.json`을 쓴다. **API 키·토큰은 JSON에 박지 말고** `${env:VAR_NAME}` 등 환경 변수로만 넘긴다.

에이전트는 `call_mcp_tool` / `fetch_mcp_resource`를 쓰기 전에 해당 서버의 도구 스키마를 확인하고, 도구가 없거나 실패하면 **실패 이유와 로컬 대안**을 남긴다.

---

## 하네스 엔지니어링

- 프롬프트가 아니라 구조로 실수를 줄인다: 테스트, 린트, 레이어 규칙, 계획 승인 게이트.
- 파이프라인 **9번(하네스)**은 렉스가 수행한다. `python -m pytest` → `ruff check .` → `mypy .` → `black .`을 **통과할 때까지** 돌리고, 실패하면 실패 로그와 함께 **담당 레이어로 되돌려** 수정 루프를 강제한다. (로컬 반복은 [AGENTS.md](AGENTS.md) **테스트 구간 실행**으로 부분 실행 가능; 게이트는 전체 통과를 원칙으로 한다.)
- 컨텍스트 지도는 `AGENTS.md`, `.cursor/rules/`, `documents/meta/CURSOR_MEMO.md`다.
- 재현된 실수는 테스트와 `documents/meta/CURSOR_MEMO.md`에 남겨 반복을 줄인다.
- 외부 기업 사례·수치·인용은 검증 가능한 출처 없이 사실처럼 단정하지 않는다.

---

## 빌드·명령

| 목적 | 명령 |
|------|------|
| 설치 | `pip install -e ".[dev]"` — 루트에 `pyproject.toml`을 두고 실행한다. |
| 실행 | `python manage.py runserver` — Django 앱 기준으로 로컬 서버를 실행한다. |
| 테스트 (전체) | `python -m pytest` |
| 테스트 (구간) | `python -m pytest -m unit` · `-m integration` · `-m shapez_solver` · `-m shapez_core` · `-m web` · `-m api` — 조합: `-m "unit and shapez_core"`. 경로만: `python -m pytest tests/unit/shapez_solver/` |
| 검증 (로컬) | `ruff check .` → `mypy .` → `black .` (포맷 적용) |
| 검증 (CI) | 동일 순서에서 **`black --check .`** 로 포맷만 검사 (파일 변경 없음) |

### 테스트 구간 실행 (pytest 마커)

전체 스위트 대신 **변경 영향 구간만** 돌릴 때는 `-m` 또는 테스트 디렉터리 경로를 쓴다.

- **마커 등록**: [`pytest.ini`](pytest.ini)의 `markers` 섹션.
- **자동 부착**: [`tests/conftest.py`](tests/conftest.py)가 수집 시 파일 경로로 `unit` / `integration` 및 `shapez_core` / `shapez_solver` / `web` / `api` 마커를 붙인다. 테스트 함수에 데코레이터를 일일이 달 필요는 없다.
- **환경**: 다른 Python과 섞이지 않도록 **`python -m pytest`**를 권장한다 (`pytest` 단독 실행과 혼용 주의).
- **하네스(렉스)**: CI·게이트에서는 원칙적으로 **전체** `python -m pytest`(또는 동등한 전체 실행)를 통과시킨다. 로컬 반복 작업만 구간 실행으로 단축한다.

---

## 파일 구조

```text
config/
django_apps/
  shapez_core/  shapez_solver/  web/
tests/
  unit/  integration/
```

---

## 완료 보고 원칙

- 변경 파일, 검증 명령, 미실행 사유를 짧게 보고한다.
- 검증 실패 시 실패한 명령, 이유, 다음 담당 캐릭터를 남긴다.
- `black .`이 파일을 바꿨으면 "검증 통과"와 별도로 "포맷 변경 발생"을 함께 보고한다.
- 위 항목을 보고한 **직후**, **이후 진행 상황**을 짧게 브리핑한다. (예: 파이프라인 상 다음 단계, 남은 이슈·후속 작업, 사용자가 할 일, 문서·승인 게이트 여부.)
- **완료 표기**: 이번 요청 범위와 검증까지 실제로 끝났을 때만 "완료"로 적는다. 남은 구현·실패한 검증·미실행 검증이 있으면 완료라고 쓰지 않고, 남은 일과 블로커를 명시한다.

검증을 못 돌렸다면 최소 아래 3가지를 남긴다.

- 실행 못 한 명령
- 이유
- 남은 위험


---

## 보안·커밋

- API 키: `.env`, 코드 하드코딩 금지
- 커밋: `[모듈] 요약`, 검증 4단계 통과 후
