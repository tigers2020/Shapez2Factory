# AGENTS.md

Cursor AI용 **shapez2Solver** 가이드 ([agents.md](https://agents.md/) 표준).

**역할**: 짧은 헌법 + **매뉴얼 라우팅** + 완료 기준. 긴 설명·persona는 넣지 않는다. 상세는 [`documents/ai/manuals/`](documents/ai/manuals/)와 [`.cursor/rules/`](.cursor/rules/root.mdc)를 읽는다.

---

## Core Rules (항상)

- 넓은 재작성 전에 **영향 파일·호출부**를 특정한다.
- 작고 검증 가능한 변경을 우선한다. 비즈니스 규칙은 **뷰/템플릿에 두지 않는다** ([architecture.mdc](.cursor/rules/architecture.mdc)).
- 코드 변경 후 **영향 구간 테스트 또는 검증 명령**을 실행하거나, 못 하면 이유·위험을 적는다.
- 단계가 나뉜 작업은 [`documents/ai/checklist.md`](documents/ai/checklist.md)를 갱신한다.
- 비밀값은 코드에 넣지 않는다 (`.env`/설정).

---

## Workflow Rules

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

추가 인덱스: [`documents/ai/README.md`](documents/ai/README.md).

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
| 테스트 전체 | `python -m pytest` |
| 테스트 구간 | `python -m pytest -m unit` 등 · 경로 예: `tests/unit/shapez_solver/` |
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
