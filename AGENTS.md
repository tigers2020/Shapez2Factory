# AGENTS.md

Cursor AI용 **shapez2Solver** 가이드 ([agents.md](https://agents.md/) 표준).

**역할**: 짧은 헌법 + **매뉴얼 라우팅** + 완료 기준. 긴 설명·persona는 넣지 않는다. 상세는 [`documents/ai/manuals/`](documents/ai/manuals/)와 [`.cursor/rules/`](.cursor/rules/root.mdc)를 읽는다.

**Cursor 하네스(요약)**: 역할 카드는 [`persona/`](persona/), 절차·규칙은 매뉴얼 + `.cursor/rules/*.mdc`, 단계·핸드오프는 [`protocols/README.md`](protocols/README.md)가 정본이다. 채팅에서 전체 워크플로를 한꺼번에 적용할 때는 선택적으로 프로젝트 Skill [`.cursor/skills/shapez2-harness/SKILL.md`](.cursor/skills/shapez2-harness/SKILL.md)를 연다. **IDE·@ 참조·MCP·스레드**만 묶어 쓸 때는 [`.cursor/skills/cursor-shapez2-harness/SKILL.md`](.cursor/skills/cursor-shapez2-harness/SKILL.md) (`@cursor-shapez2-harness`)를 연다.

**에이전트 네이티브 엔지니어링(요약)**: 인간의 역할은 타이핑보다 **의도·아키텍처·검증·디버깅**에 두는 것을 전제로 한다. 의도를 구체화(파일·심볼·완료 조건·제약)하고, **이해·재현 없이 수정하지 않으며**, 스레드·서브에이전트로 **컨텍스트를 분리**하고, 계측·가설·회귀 테스트로 검증한다. **규칙(Rules)** 은 상시 지시, **스킬(Skills)** 은 온디맨드 워크플로다. 상세·체크리스트: [`documents/ai/manuals/cursor_usage.md`](documents/ai/manuals/cursor_usage.md).

---

## Core Rules (항상)

- 넓은 재작성 전에 **영향 파일·호출부**를 특정한다.
- 작고 검증 가능한 변경을 우선한다. 비즈니스 규칙은 **뷰/템플릿에 두지 않는다** ([architecture.mdc](.cursor/rules/architecture.mdc)).
- 코드 변경 후 **영향 구간 테스트 또는 검증 명령**을 실행하거나, 못 하면 이유·위험을 적는다.
- 단계가 나뉜 작업은 [`documents/ai/checklist.md`](documents/ai/checklist.md)를 갱신한다.
- 비밀값은 코드에 넣지 않는다 (`.env`/설정).

---

## Workflow Rules

### 문서 Authority

- 문서 context를 잡을 때는 먼저 [`documents/ai/START_HERE.md`](documents/ai/START_HERE.md), [`documents/index/document_inventory.md`](documents/index/document_inventory.md), [`documents/index/document_lifecycle.md`](documents/index/document_lifecycle.md)를 확인한다.
- `CANON` 문서만 현재 시스템 계약으로 본다. `ACTIVE`는 진행 중 플랜, `RESEARCH`는 근거, `REPORT`는 관측 결과이며 정본이 아니다.
- `ARCHIVED`·`SUPERSEDED` 문서는 역사 확인용으로만 읽고, 구현 판단에 쓰지 않는다.

### 작업 전 (Before)

1. **작업 유형**을 하나 고른다: django · solver · graph UI · frontend · tests · refactor · database.
2. 아래 **Manual Routing**에서 해당 [`documents/ai/manuals/*.md`](documents/ai/manuals/)를 연다 (필요한 챕터만).
3. 의미 있는 변경이면 프로젝트 게이트대로 **리서치·플랜(`documents/`)·사람 승인** 후 구현 ([protocols/README.md](protocols/README.md)). 진행 중에는 필요 시 다음을 갱신한다.
   - [`documents/ai/current_plan.md`](documents/ai/current_plan.md) — 이번 목표·범위
   - [`documents/ai/context_notes.md`](documents/ai/context_notes.md) — 가정·결정·링크
   - [`documents/ai/checklist.md`](documents/ai/checklist.md) — 단계·완료 표시

### 작업 중 (During)

- `.cursor/rules/root.mdc` **코드 단순성**과 매뉴얼의 레이어 규칙을 따른다.
- 구현 단계 워크플로: [.cursor/rules/persona-dialogue.mdc](.cursor/rules/persona-dialogue.mdc).

### 작업 후 (After — Quality Gate)

- 변경 파일 목록, 변경 이유, 실행한 테스트·검증 (`pytest` / `ruff` / `mypy` / `black`).
- [`documents/ai/checklist.md`](documents/ai/checklist.md) 최종 반영.
- 상세 체크리스트: 매뉴얼 [`testing.md`](documents/ai/manuals/testing.md) 및 본문 아래 **완료 조건**.

---

## Manual Routing

| 작업 유형 | 읽을 매뉴얼 |
|-----------|-------------|
| Django, 뷰, URL, 앱 배치 | [`documents/ai/manuals/django.md`](documents/ai/manuals/django.md) |
| 솔버·레시피 그래프 로직·`shapez_solver` | [`documents/ai/manuals/solver.md`](documents/ai/manuals/solver.md) |
| 레시피 그래프 에디터·노드 시각화·혼동 방지 | [`documents/ai/manuals/graph_ui.md`](documents/ai/manuals/graph_ui.md) |
| 템플릿·정적 자산·프론트 빌드(Recipe Graph 등) | [`documents/ai/manuals/frontend.md`](documents/ai/manuals/frontend.md) |
| 테스트·pytest·마커 | [`documents/ai/manuals/testing.md`](documents/ai/manuals/testing.md) |
| 리팩터·삭제·최소 침습 | [`documents/ai/manuals/refactor.md`](documents/ai/manuals/refactor.md) |
| 모델·마이그레이션·DB | [`documents/ai/manuals/database.md`](documents/ai/manuals/database.md) |
| 데이터 파이프라인 설계(스키마·ETL·검증·모니터링) | [`database.md`](documents/ai/manuals/database.md) · Skill [`.cursor/skills/data-pipeline-harness/SKILL.md`](.cursor/skills/data-pipeline-harness/SKILL.md) (`@data-pipeline-harness`) |
| 종합 코드 리뷰(아키텍처·보안·성능·스타일 병렬 감사) | [`refactor.md`](documents/ai/manuals/refactor.md) · Skill [`.cursor/skills/code-review-harness/SKILL.md`](.cursor/skills/code-review-harness/SKILL.md) (`@code-review-harness`) |
| 리서치(웹·학술·커뮤니티, 교차검증·종합 보고) | [`document_lifecycle.md`](documents/index/document_lifecycle.md) · [`START_HERE.md`](documents/ai/START_HERE.md) · Skill [`.cursor/skills/research-harness/SKILL.md`](.cursor/skills/research-harness/SKILL.md) (`@research-harness`) |
| Cursor 사용 습관·컨텍스트·요금 절약 | [`documents/ai/manuals/cursor_usage.md`](documents/ai/manuals/cursor_usage.md) |

추가 인덱스: [`documents/ai/README.md`](documents/ai/README.md).

---

## MCP: Serena (코드베이스)

**Serena** (`user-serena` MCP)는 로컬에서 LSP 기반 시맨틱 분석(클래스·함수·호출·상속), 심볼 단위 삽입·수정·리네임, 필요한 심볼만 선택 전달로 컨텍스트를 줄이는 도구다. 코드는 외부로 나가지 않는다.

- **계약**: 코딩 작업에 Serena를 쓸 때는 서버 지시에 따라 **`initial_instructions`** 도구로 Serena 매뉴얼을 **먼저** 읽는다. 도구 스키마는 `mcps/user-serena/tools/`를 본다.
- **페르소나**: **[시몬]**이 영향 범위·광역 탐색이 필요하면 브리핑에 Serena 활용을 명시한다. **[도미닉·유리·아다]**는 담당 레이어에서 호출·참조·경계를 잡을 때 전 파일 로드·무차별 검색보다 Serena를 **우선 고려**한다.
- 다른 MCP·선택 사용 원칙: [`.cursor/rules/mcp.mdc`](.cursor/rules/mcp.mdc).

---

## 상세 매뉴얼 · 규칙 파일

- AI 작업 기억·체크리스트: [`documents/ai/`](documents/ai/)
- 실행 규칙(항상 적용): [`.cursor/rules/root.mdc`](.cursor/rules/root.mdc), [`architecture.mdc`](.cursor/rules/architecture.mdc), [`persona-dialogue.mdc`](.cursor/rules/persona-dialogue.mdc), [`karpathy-guidelines.mdc`](.cursor/rules/karpathy-guidelines.mdc)
- 파이프라인·페르소나 카드: [`protocols/README.md`](protocols/README.md), [`persona/README.md`](persona/README.md)
- 도메인·게임 참고: [`documents/research/research_shapez2_game_systems_2026-05-01.md`](documents/research/research_shapez2_game_systems_2026-05-01.md)

규칙 우선순위: `root.mdc` → `architecture.mdc` → `mcp.mdc` → `cursor-usage.mdc` → `persona-dialogue.mdc` → `karpathy-guidelines.mdc` → 기타 glob.

---

## 빌드 · 테스트 · 검증 (요약)

| 목적 | 명령 |
|------|------|
| 설치 | `pip install -e ".[dev]"` |
| 서버 | `python manage.py runserver` |
| 테스트 전체 | `python -m pytest` (병렬: `python -m pytest -n auto --dist loadscope`) |
| 테스트 구간 | `python -m pytest -m unit` · `-m "not slow"` · 경로 예: `tests/unit/shapez_solver/` · 루트 `Makefile` (`make test-fast` 등) |
| 로컬 검증 | `ruff check .` → `mypy .` → `black .` |
| CI 포맷 | `black --check .` |

마커·자동 부착: [`pytest.ini`](pytest.ini), [`tests/conftest.py`](tests/conftest.py). 자세한 표는 [`documents/ai/manuals/testing.md`](documents/ai/manuals/testing.md).

---

## `documents/` 작성 언어

프로젝트 Markdown 본문은 **한국어**(코드·경로·CLI·식별자·URL은 그대로).

---

## 명시적 승인 없이 하지 말 것

대규모 폴더 이동 · DB 스키마/마이그레이션 · 미증명 레거시 삭제 · 솔버 핵심 전면 교체 · 공개 URL/API 계약 깨기. 플랜 게이트가 있으면 그에 따른다.

---

## 완료 조건 (요약)

- 변경 파일·이유·검증(또는 미실행 사유·위험).
- `black`으로 파일이 바뀌었으면 별도 명시.
- **이후 진행 상황** 한 덩어리. 실제로 끝났을 때만 「완료」.

---

## 레포 구조 (참고)

```text
config/
django_apps/
  shapez_core/  shapez_solver/  web/
tests/
  unit/  integration/
documents/
  ai/           ← AI 매뉴얼·현재 계획·체크리스트
```

---

## Cursor Cloud specific instructions

- **Single service**: Django dev server only. No Docker, Redis, Celery, or external DB required.
- **Database**: SQLite (default). Run `python3 manage.py migrate` after first install to create `db.sqlite3`. Migrations are idempotent.
- **Dev server**: `python3 manage.py runserver 0.0.0.0:8000`. Use `python3` (not `python`) as `python` is not on PATH in the Cloud VM.
- **PATH**: Dev tool binaries (`black`, `ruff`, `mypy`, `pytest`) install to `/home/ubuntu/.local/bin`. Prepend to PATH: `export PATH="/home/ubuntu/.local/bin:$PATH"`.
- **Solver API** (`POST /api/solver/solve/`): Requires CSRF token. Fetch a page first to get `csrftoken` cookie, then send `X-CSRFToken` header + cookie.
- **Pre-built frontend assets**: CSS/JS bundles are committed. `npm install` / `npm run build` only needed if modifying frontend source (`assets/css/`, `frontend/`).
- **Graph preview renderer**: Defaults to `playwright_png` which requires Node + Playwright. Set `SOLVER_GRAPH_PREVIEW_RENDERER=noop` in `.env` to skip (3D preview still works in-browser). Tests pass without Playwright.
- **Lint/test commands**: See **빌드 · 테스트 · 검증** table above. `black --check .` currently reports 1 pre-existing formatting issue in `django_apps/web/views/macro_staff.py`.
