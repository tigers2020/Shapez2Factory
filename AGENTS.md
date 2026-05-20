# AGENTS.md

## Mission

이 저장소의 목표는 **shapez2 Factory Planner** 이다.
당신은 항상 **작은 안전한 변경 + 빠른 검증 + 문서 동기화** 원칙으로 행동한다.

상시 규칙(Caveman 6절·게이트·검증·Forbidden): [`.cursor/rules/shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc)  
절차·컨텍스트·Cloud VM: [`documents/ai/manuals/cursor_usage.md`](documents/ai/manuals/cursor_usage.md)  
파이프라인 정본: [`protocols/README.md`](protocols/README.md)  
구현 오케스트레이션: [`@shapez2-workflow`](.cursor/skills/shapez2-workflow/SKILL.md)

## Trigger

- 새 기능 요청 / 버그 리포트 / 테스트 실패 / 리팩터 요청 / 성능·안정성 개선

## Repository map

| 경로 | 목적 |
|---|---|
| `config/`, `manage.py` | Django 설정·진입 |
| `django_apps/shapez_core/` | shape 규칙·파싱·preview (도미닉) |
| `django_apps/shapez_solver/` | recipe graph·planner·solver (유리) |
| `django_apps/asteroid_lab/` | 소행성 실험실·replay·optimization (유리) |
| `django_apps/web/` | UI·템플릿·정적 (지나) |
| `tests/` | unit / integration / golden (테스) |
| `frontend/` | React Flow editor 등 |
| `documents/` | CANON·플랜·리서치 정본 |
| `src/shapez2_factory/` | Phase 2+ hexagonal 추출 목표 |

참조: [`structure.md`](structure.md) · [`docs/`](docs/) · [`.cursor/rules/`](.cursor/rules/) · [`.cursor/skills/`](.cursor/skills/)

## Required workflow

1. 관련 `docs/`, `documents/` 정본·코드를 읽고 문제를 재정의한다.
2. Plan Mode로 변경 대상·리스크·검증 방법을 정리하고 **사람 승인**을 받는다.
3. 가장 작은 단위로 구현한다.
4. 변경 후 검증을 실행한다 ([shapez2-core.mdc](.cursor/rules/shapez2-core.mdc) Dual Gate).
5. 동작·설계가 바뀌면 `docs/`·`documents/` plan을 갱신한다.
6. 마감: [shapez2-core.mdc Caveman 6절](.cursor/rules/shapez2-core.mdc) 필수.

## Manual Routing

| 작업 유형 | 매뉴얼 |
|-----------|--------|
| Django · 뷰 · URL | [django.md](documents/ai/manuals/django.md) |
| 솔버 · `shapez_solver` | [solver.md](documents/ai/manuals/solver.md) |
| 그래프 UI · 노드 시각화 | [graph_ui.md](documents/ai/manuals/graph_ui.md) |
| 템플릿 · 정적 · 프론트 빌드 | [frontend.md](documents/ai/manuals/frontend.md) |
| 테스트 · pytest · TDD · 게이트 | [testing.md](documents/ai/manuals/testing.md) |
| 리팩터 · 최소 침습 | [refactor.md](documents/ai/manuals/refactor.md) |
| DB · 마이그레이션 | [database.md](documents/ai/manuals/database.md) |
| Cursor · 컨텍스트 · Cloud | [cursor_usage.md](documents/ai/manuals/cursor_usage.md) |

TDD 상세·Forbidden shortcuts: [testing.md](documents/ai/manuals/testing.md)  
Asteroid Lab 불변식: [asteroid-lab-invariants.mdc](.cursor/rules/asteroid-lab-invariants.mdc)

## Permissions

| 권한 유형 | 내용 |
|-----------|------|
| 기본 | 읽기·검색·계획 수립 |
| 허용 쓰기 | workspace 내부 소스·테스트·문서 |
| 사람 승인 필요 | `.env`·`pyproject.toml` 대형 변경 / CI·배포 / 보안·권한 / 대규모 rename·delete |
| 금지 | secrets 노출 / 생성 산출물 직접 수정 / 검증 없이 완료 선언 |

## BLOCKED 형식

도메인 충돌·검증 명령 미발견·기준 테스트 없는 회귀·고위험 변경 시:

```
BLOCKED:
- missing context:
- risky change:
- recommended next step:
```

## Definition of done

- 요청 범위를 벗어나지 않았다.
- 테스트·빌드·검증 결과가 제시되었다.
- 실패한 검증이 남아 있으면 명시되었다.
- 문서와 코드가 서로 모순되지 않는다.

## References

| 항목 | 경로 |
|------|------|
| 상시 규칙 | [shapez2-core.mdc](.cursor/rules/shapez2-core.mdc) |
| 레이어·앱 소유 | [architecture.mdc](.cursor/rules/architecture.mdc) |
| 저장소 구조 | [structure.md](structure.md) |
| AI 허브 | [documents/ai/](documents/ai/) |
| 페르소나 | [persona/](persona/) |
| 게임 근거 | [research_shapez2_game_systems_2026-05-01.md](documents/research/research_shapez2_game_systems_2026-05-01.md) |

**우선순위**: `AGENTS.md` → `shapez2-core.mdc` → glob 규칙.
