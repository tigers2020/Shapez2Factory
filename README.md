# {{PROJECT_NAME}}

> Cursor를 "코드 작성기"가 아니라 **하니스 실행기**로 다루는 프로젝트. 루트 `AGENTS.md`로 운영 계약을 만들고, `.cursor/rules/`로 경로별 가이드를 붙이며, `.cursor/skills/`로 반복 업무를 패키징하고, `docs/domain/`과 `tests/golden/`으로 지식과 검증을 외부화한다. — [research.md](research.md) 결론

## Quick Start

```bash
# 1. 개발 의존성 설치
pip install -e ".[dev]"

# 2. 검증 체인 실행 (렉스 4단계; pytest -q/--quiet/--tb=no 금지)
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

모든 단계가 통과하면 개발 환경이 정상이다.

## Directory Map

```
{{PROJECT_NAME}}/
├── AGENTS.md                        # 운영 계약서 (최우선 참조)
├── pyproject.toml                   # Python 3.12, ruff/black/mypy/pytest 설정
├── .cursorignore                    # AI 컨텍스트 제외 목록
├── .cursor/
│   ├── rules/                       # 경로별 기계 친화 규칙 (.mdc)
│   └── skills/                      # 반복 작업 스킬 패키지
├── src/{{package_name}}/
│   ├── domain/                      # 순수 비즈니스 규칙 (도미닉)
│   ├── application/
│   │   ├── ports/                   # Port 추상화 (Protocol/ABC)
│   │   └── use_cases/               # Use case 오케스트레이션 (유리)
│   ├── adapters/                    # 외부 시스템 구현 (아다)
│   ├── interfaces/                  # UI 화면·상태 (지나)
│   └── bootstrap/                   # 의존성 조립 (시몬)
├── tests/
│   ├── unit/                        # Domain + use case 단위 테스트
│   ├── integration/                 # Adapter 통합 테스트
│   └── golden/                      # 결정적 회귀 데이터 (phase2)
├── docs/
│   ├── domain/                      # 도메인 매뉴얼 (도미닉)
│   ├── architecture/                # 레이어 구조·의존 방향
│   ├── runbooks/                    # 반복 개발 절차
│   └── adr/                         # 아키텍처 결정 기록
├── persona/                         # Position lenses (domain routing)
├── protocols/                       # Spec-first workflow stages
├── documents/ai/templates/          # Contract brief + PR plan templates
├── documents/                       # 메모, 플랜, 리서치 문서
└── .github/workflows/ci.yml         # GitHub Actions CI
```

## Architecture

의존 방향: `interfaces` → `application` → `domain` ← (adapters → ports)

상세: [docs/architecture/README.md](docs/architecture/README.md)

## Workflow

**Spec-first · Small PR · Test-gated · Review-driven** ([`AGENTS.md`](AGENTS.md))

```text
Problem → Contract brief → PR plan (one purpose) → Failing tests → Minimal implementation → Gate → Review → Merge
```

1. Read [`AGENTS.md`](AGENTS.md) + CANON spec for the task.
2. Fill [`contract-brief.md`](documents/ai/templates/contract-brief.md) or link spec.
3. Scope one PR ([`pr-plan.md`](documents/ai/templates/pr-plan.md)).
4. Failing test before production (contract/regression).
5. Run dual gate ([`testing.md`](documents/ai/manuals/testing.md)).
6. Sync docs when public contract changes.

Stages: [`protocols/README.md`](protocols/README.md) · Rule: [`.cursor/rules/workflow.mdc`](.cursor/rules/workflow.mdc)

## Position lenses

| Lens | Card | Ownership |
|---|---|---|
| Coordinator | [simon.md](persona/simon.md) | Scope · PR sequence |
| Domain | [dominic.md](persona/dominic.md) | `domain/` |
| Application | [yuri.md](persona/yuri.md) | `application/` |
| Adapters | [ada.md](persona/ada.md) | `adapters/` |
| Tests | [tess.md](persona/tess.md) | `tests/` |
| Harness | [rex.md](persona/rex.md) | pytest · ruff · mypy · black |
| UI | [gina-gui.md](persona/gina-gui.md) | `interfaces/`, web |
| Django | [denny.md](persona/denny.md) | `django_apps/`, `config/` |

Index: [persona/README.md](persona/README.md) — routing hints, not roleplay.

## Pipeline

Workflow stages: [protocols/README.md](protocols/README.md)

## Roadmap

| Phase | 내용 |
|---|---|
| Phase 1 (현재) | 운영 계약·규칙·스킬·문서 골격 |
| Phase 2 | `tests/golden/`, `harness/validators/` — 검증 확보 |
| Phase 3 | `feature-add`·`refactor` 스킬, `.cursor/hooks.json` 자동 루프 |
| Phase 4~5 | MCP, Bugbot, Cloud Agent |
