# shapez2Solver repository structure

이 저장소는 Django-first 프로젝트다. 런타임 소유권은 `config/`, `manage.py`, `django_apps/`에 있고, 테스트는 `tests/unit/`과 `tests/integration/`으로 나뉜다.

## Top-level layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | 에이전트/기여자 라우팅, 품질 게이트, 매뉴얼 인덱스 |
| `config/` | Django 설정, 루트 URL, WSGI/ASGI, 런타임 플래그 |
| `django_apps/shapez_core/` | shape 파싱, 정규화, preview API, canonical game data |
| `django_apps/shapez_solver/` | solver 프로젝트/런 모델, recipe graph, macro pattern, planner 서비스 |
| `django_apps/shapez_asteroid/` | asteroid extraction, copy-preview, mining layout v2 파이프라인 |
| `django_apps/web/` | 페이지 템플릿, 정적 자산, thin view, staff tooling |
| `tests/unit/` | core/solver/asteroid/web 단위 테스트 |
| `tests/unit/shapez_asteroid_v2/` | mining layout v2 계약/경계/placement/routing/replay 테스트 |
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

`node_modules/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.graph_preview_cache*/`, `db.sqlite3`, `.env`, `v2_behavior_artifact_*.json`은 로컬/생성 산출물이며 구조 정본이 아니다.

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

### `django_apps/shapez_asteroid/`

- `extraction/`: blueprint decoding, grid-coordinate authority, asteroid extraction DTO.
- `services/asteroid_mining_layout_v2/`: 현재 mining layout 구현 권위. STEP0 decode, STEP1 reconstruction, Pass1/Pass2 placement, STEP4 routing, validation, replay/serialization 경계를 포함한다.
- `services/asteroid_mining_layout_v2/adapters/`: mining-map row와 외부 DTO 사이의 adapter boundary.
- `services/asteroid_mining_layout_v2/decode/`: copy decode adapter와 existing layout analysis.
- `services/asteroid_mining_layout_v2/domain/`: v2 DTO, enum, grid, orchestration, decoded blueprint, corridor, trace semantics.
- `services/asteroid_mining_layout_v2/reconstruction/`: asteroid reconstruction, diagnostics, interior patch.
- `services/asteroid_mining_layout_v2/placement/`: bundle candidate, Pass1 outer placement, Pass2 internal placement, corridor opening, placement FSM.
- `services/asteroid_mining_layout_v2/routing/`: trunk seed, connectivity, merge-aware router, corridor probe, STEP4 corridor recovery.
- `services/asteroid_mining_layout_v2/replay/`, `runtime/`, `serialization/`: output-only trace/replay/runtime/public artifact contracts.
- `services/asteroid_mining_layout/` 계열 v1 문서·계획은 [`documents/archive/2026-05-mining-layout-v1-era/`](documents/archive/2026-05-mining-layout-v1-era/README.md)로 분류한다.
- `ports/`: solver input/output adapter boundary.
- `views.py` + `urls.py`: `/api/asteroid/health/` 및 asteroid page/API 연동.

### `django_apps/web/`

- `views.py`, `views/`: public pages, gallery, demo, support, asteroid mining, solver UI, pattern lab, staff macro-pattern flows.
- `services/graph_preview.py`: graph preview asset/cache helper.
- `social_adapter.py`, `socialaccount_forms.py`: django-allauth/social account hooks.
- `templates/web/`: page templates and partials.
- `static/web/`: Tailwind output CSS, JS bundles, solver timeline, GLTF preview, staff scripts, vendor assets.

## URL ownership

Root routing (`config/urls.py`):

| Path | Owner |
|---|---|
| `/admin/` | Django admin |
| `/i18n/` | Django language switching |
| `/accounts/` | django-allauth |
| `/api/` | `django_apps.shapez_core` |
| `/api/asteroid/` | `django_apps.shapez_asteroid` |

Internationalized routes (`i18n_patterns`, default language without prefix) include `django_apps.web` pages such as `/`, `/gallery/`, `/demo/`, `/support/`, `/asteroid/`, `/solver/`, `/solver/pattern-lab/`, staff macro-pattern URLs, auth shortcuts, `/solve/`, and graph-preview cache URLs.

## Test layout

- `tests/unit/shapez_core/`: parser, render scene, SVG preview, geometry.
- `tests/unit/shapez_solver/`: solver engine, recipe graph, models, catalog, pattern lab.
- `tests/unit/shapez_asteroid/`: archived/v1-era asteroid solver and shared compatibility checks where still retained.
- `tests/unit/shapez_asteroid_v2/`: v2 namespace, domain DTO, reconstruction, placement, corridor probe/recovery, trace/replay, serialization, validation contract tests.
- `tests/unit/web/`: template/markup and web-specific checks.
- `tests/integration/api/`: health/API integration checks.
- `tests/integration/web/`: page smoke, auth, pattern lab, macro-pattern staff flows.

## Documents map

- [`documents/README.md`](documents/README.md): canonical document index and active-vs-archive comparison.
- [`documents/index/document_lifecycle.md`](documents/index/document_lifecycle.md): `CANON`, `ACTIVE`, `RESEARCH`, `REPORT`, `COMPLETED`, `ARCHIVED`, `SUPERSEDED` definitions.
- [`documents/index/document_inventory.md`](documents/index/document_inventory.md): current authority inventory.
- [`documents/ai/`](documents/ai/README.md): current plan, context notes, checklist, manuals, active AI plans.
- [`documents/Algorithm/mining_solver_cursor_sessions/`](documents/Algorithm/mining_solver_cursor_sessions/README.md): current mining solver canonical step specs.
- [`documents/plans/`](documents/plans/): active or not-yet-confirmed implementation plans.
- [`documents/research/`](documents/research/): active research and domain evidence.
- [`documents/reports/`](documents/reports/): observation/debug/audit reports, not canonical contracts.
- [`documents/archive/`](documents/archive/README.md): completed, obsolete, superseded, or reference-only document sets.

## Common commands

| Goal | Command |
|---|---|
| Install dev dependencies | `pip install -e ".[dev]"` |
| Run Django locally | `python manage.py runserver` |
| Run tests | `python -m pytest` |
| Run unit tests | `python -m pytest -m unit` |
| Run v2 asteroid tests | `python -m pytest tests/unit/shapez_asteroid_v2/` |
| Static analysis | `ruff check .` |
| Type-check | `mypy .` |
| Format check | `black --check .` |
| Build CSS | `npm run build:css` |
| Build Recipe Graph editor | `npm run build:recipe-graph-editor` |
