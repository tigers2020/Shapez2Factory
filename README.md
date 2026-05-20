# shapez2 Factory Planner

> Cursor를 "코드 작성기"가 아니라 **하니스 실행기**로 다루는 프로젝트. 루트 `AGENTS.md`로 운영 계약을 만들고, `.cursor/rules/`로 경로별 가이드를 붙이며, `.cursor/skills/`로 반복 업무를 패키징하고, `docs/domain/`과 `tests/golden/`으로 지식과 검증을 외부화한다.

## Quick Start

```bash
# 1. 의존성 설치
pip install -e ".[dev]"

# 2. 로컬 DB (선택)
# set DJANGO_USE_SQLITE=1

# 3. 검증 체인 (PR full gate — testing.md 정본)
python -m ruff check .
python -m black --check .
python -m mypy src
python -m pytest -q

# 4. 개발 서버
python manage.py runserver
```

## Directory Map

```
shapez2 Factory Planner/
├── AGENTS.md                        # 운영 계약서 (최우선 참조)
├── manage.py / config/              # Django 진입 (Phase 1 런타임)
├── django_apps/
│   ├── shapez_core/                 # shape 규칙·파싱·preview
│   ├── shapez_solver/               # recipe graph·planner
│   ├── asteroid_lab/                # 소행성 실험실·replay
│   └── web/                         # UI·템플릿·정적
├── src/shapez2_factory/             # hexagonal 추출 목표 (Phase 2+, 현재 stub)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── golden/                      # phase2
├── docs/                            # 에이전트 친화 요약
├── documents/                       # CANON·플랜·리서치 정본
├── frontend/                        # React Flow editor 등
├── persona/                         # 팀 페르소나 카드
├── protocols/                       # 10단계 파이프라인
└── .github/workflows/ci.yml
```

## Architecture

- **현재**: Django-first — [`structure.md`](structure.md), [`docs/architecture/README.md`](docs/architecture/README.md)
- **목표**: `src/shapez2_factory/` hexagonal layers (점진 추출)

## Workflow

1. `AGENTS.md`와 관련 `docs/`·`documents/`를 먼저 읽는다.
2. 변경 대상·리스크·검증 방법을 계획한다.
3. 가장 작은 단위로 구현한다.
4. [testing.md](documents/ai/manuals/testing.md) full gate를 실행한다.
5. 문서를 동기화한다.

## Team Personas

| 이름 | 역할 |
|---|---|
| 시몬 | 분배·조율, 구현 게이트 |
| 도미닉 | domain — 비즈니스 규칙 |
| 유리 | application — use case, ports |
| 아다 | adapters — 외부 시스템 |
| 테스 | tests — QA |
| 렉스 | CI/검증 체인 |
| 지나 | interfaces — UI |

인덱스: [persona/README.md](persona/README.md)

## Pipeline

10단계 파이프라인 정본: [protocols/README.md](protocols/README.md)

## Roadmap

| Phase | 내용 |
|---|---|
| Phase 1 (현재) | 운영 계약·규칙·문서 하이브리드 정렬; Django 런타임 유지 |
| Phase 2 | `tests/golden/`, `harness/validators/` |
| Phase 3 | `src/shapez2_factory/` 도메인 추출 시작 |
| Phase 4~5 | MCP, hooks, Cloud Agent |
