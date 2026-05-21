# shapez2 Factory Planner repository structure

이 저장소는 Django-first 프로젝트다. 런타임 소유권은 `config/`, `manage.py`, `django_apps/`에 있고, 테스트는 `tests/unit/`과 `tests/integration/`으로 나뉜다.

## Documentation layers

| 트리 | 역할 |
|---|---|
| [`AGENTS.md`](AGENTS.md) | 에이전트 운영 계약 (최우선) |
| [`docs/`](docs/) | domain·architecture·runbook·ADR **요약** (에이전트 친화) |
| [`documents/`](documents/README.md) | CANON·플랜·리서치 **정본** |
| [`structure.md`](structure.md) | 저장소 경로·앱·URL·테스트 배치 (본 문서) |
| [`src/shapez2_factory/`](src/shapez2_factory/) | Phase 2+ hexagonal 추출 목표 (현재 stub) |

## Top-level layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | 에이전트/기여자 운영 계약, 품질 게이트, 매뉴얼 인덱스 |
| `docs/` | domain·architecture·runbook·ADR 요약 |
| `src/shapez2_factory/` | hexagonal 추출 목표 (Phase 2+, stub) |
| `config/` | Django 설정, 루트 URL, WSGI/ASGI, 런타임 플래그 |
| `django_apps/shapez_core/` | shape 파싱, 정규화, preview API, canonical game data |
| `django_apps/shapez_solver/` | solver 프로젝트/런 모델, recipe graph, macro pattern, planner 서비스 |
| `django_apps/asteroid_lab/` | 소행성 실험실(ORM·디코드·리플레이; 레시피 솔버와 별도) |
| `django_apps/web/` | 페이지 템플릿, 정적 자산, thin view, staff tooling |
| `tests/unit/` | core/solver/web/asteroid_lab 등 단위 테스트 |
| `tests/integration/` | Django request/response, page/API integration smoke |
| `documents/` | 문서 authority, 계획, 연구, 보고, archive. 정본 지도는 [`documents/README.md`](documents/README.md) |
| `protocols/` | multi-step pipeline 절차 ([`protocols/README.md`](protocols/README.md)) |
| `persona/` | 역할 카드와 라우팅 ([`persona/README.md`](persona/README.md)) |
| `.cursor/` | Cursor rules, skills, plans, editor guidance |
| `assets/css/` | Tailwind input CSS source |
| `frontend/recipe_graph_editor/` | Vite + React Flow editor source |
| `frontend/graph_layout/` | TypeScript graph layout engine source |
| `locale/` | gettext catalog |
| `scripts/` | locale, graph-preview, diagnostics helper scripts |
| `var/` | 로컬 실행 trace/debug 산출물. 소스 정본 아님 |

`node_modules/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.graph_preview_cache*/`, `db.sqlite3`, `.env`는 로컬/생성 산출물이며 구조 정본이 아니다.

## Django app ownership

### `django_apps/shapez_core/`

- `domain/`: shape primitives, catalog, operations, crystal geometry, shape patterns.
- `services/`: shape code parser, codec, render scene, SVG preview thumbnail, preview response composition.
- `views.py` + `urls.py`: `/api/health/`, `/api/shape-preview/`.

### `django_apps/shapez_solver/`

- `models.py`: persisted solver projects/runs, macro pattern/recipe graph storage.
- `domain/`: operation metadata, factory demand, search cost 등 solver-side domain helper.
- `services/`: operation engine, recipe graph adapters/validation, planner/scaffold, pattern lab, catalog repository.
- `dto/`: solver-facing DTO.
- Solver UI와 관련 JSON endpoint는 `django_apps.web` route를 통해 제공된다.

### `django_apps/asteroid_lab/`

- 소행성 맵 입력·디코드 스냅샷·리플레이 트랙 등 실험실 데이터 모델과 서비스.
- `django_apps.shapez_asteroid`(제거됨) 및 채굴 레이아웃 솔버 패키지에 **의존하지 않는다**(경계 테스트로 고정).

### `django_apps/game_data/`

- `models/`: canonical game dump ORM (concrete fields, relations, constraints; no domain `JSONField`).
- `importers/`: deterministic `GameDataImporter` and section importers.
- `services/`: classifiers, identifiers, `validators`, import guards.
- `browse/`: staff browse dashboard (`registry.py`, thin `views.py`, `urls.py`).
- `admin.py`: aggregate-root `ModelAdmin` and inlines aligned with `browse/registry.py` specs.
- Tests: `tests/unit/game_data/`.

### `django_apps/web/`

- `views.py`, `views/`: public pages, gallery, demo, support, asteroid mining lab UI, solver UI, pattern lab, staff macro-pattern flows.
- `services/graph_preview.py`: graph preview asset/cache helper.
- `social_adapter.py`, `socialaccount_forms.py`: django-allauth/social account hooks.
- `templates/web/`: page templates and partials.
- `static/web/`: Tailwind output CSS, JS bundles, solver timeline, GLTF preview, staff scripts, vendor assets.

## URL ownership

Root routing (`config/urls.py`):

| Path | Owner |
|---|---|
| `/admin/game-data/` | `django_apps.game_data.browse` |
| `/admin/` | Django admin |
| `/i18n/` | Django language switching |
| `/accounts/` | django-allauth |
| `/api/` | `django_apps.shapez_core` |

Internationalized routes (`i18n_patterns`, default language without prefix) include `django_apps.web` pages such as `/`, `/gallery/`, `/demo/`, `/support/`, `/asteroid-miner-layout/`, `/solver/`, `/solver/pattern-lab/`, staff macro-pattern URLs, auth shortcuts, `/solve/`, and graph-preview cache URLs.

## Test layout

- `tests/unit/shapez_core/`: parser, render scene, SVG preview, geometry.
- `tests/unit/shapez_solver/`: solver engine, recipe graph, models, catalog, pattern lab.
- `tests/unit/asteroid_lab/`: 실험실 ORM·디코드·서비스 경계.
- `tests/unit/game_data/`: import, models, admin browse, JSON ban, simulation contracts.
- `tests/unit/architecture/`: Django app import boundary matrix.
- `tests/unit/web/`: template/markup and web-specific checks.
- `tests/integration/api/`: health/API integration checks.
- `tests/integration/web/`: page smoke, auth, pattern lab, macro-pattern staff flows.

## Documents map

- [`documents/README.md`](documents/README.md): canonical document index and active-vs-archive comparison.
- [`documents/index/document_lifecycle.md`](documents/index/document_lifecycle.md): `CANON`, `ACTIVE`, `RESEARCH`, `REPORT`, `COMPLETED`, `ARCHIVED`, `SUPERSEDED` definitions.
- [`documents/index/document_inventory.md`](documents/index/document_inventory.md): current authority inventory.
- [`documents/ai/`](documents/ai/README.md): current plan, context notes, checklist, manuals, active AI plans.
- [`documents/Algorithm/README.md`](documents/Algorithm/README.md): algorithm 문서 슬롯(현재 채굴 솔버 정본 없음).
- [`documents/plans/`](documents/plans/): active or not-yet-confirmed implementation plans.
- [`documents/research/`](documents/research/): active research and domain evidence.
- [`documents/reports/`](documents/reports/README.md): observation/debug/audit reports, not canonical contracts.
- [`documents/archive/`](documents/archive/README.md): completed, obsolete, superseded, or reference-only document sets.

## Common commands

| Goal | Command |
|---|---|
| Install dev dependencies | `pip install -e ".[dev]"` |
| Run Django locally | `python manage.py runserver` |
| Run tests (default: scope to your change) | `python -m pytest <path-to-test-file-or-dir>` |
| Run full test suite | `python -m pytest` — use before merge/release or when broad regression is needed |
| Run unit tests | `python -m pytest -m unit` |
| Run asteroid lab tests | `python -m pytest tests/unit/asteroid_lab/` |
| Static analysis | `ruff check .` |
| Type-check | `mypy django_apps config src` |
| Format check | `black --check .` |
| Build CSS | `npm run build:css` |
| Build Recipe Graph editor | `npm run build:recipe-graph-editor` |
