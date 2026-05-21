# 매뉴얼: Django · 백엔드

작업 전 [`AGENTS.md`](../../../AGENTS.md) Core Rules를 확인한다.

## 소유

| 앱 | 경로 | 책임 |
|----|------|------|
| shapez_core | `django_apps/shapez_core/` | 도형 규칙·파싱·정규화 |
| shapez_solver | `django_apps/shapez_solver/` | 솔버 유스케이스·서비스 |
| asteroid_lab | `django_apps/asteroid_lab/` | 소행성 실험실(ORM·디코드·리플레이; 레시피 솔버와 별도) |
| web | `django_apps/web/` | 템플릿·정적 자산·얇은 뷰 |
| game_data | `django_apps/game_data/` | 게임 덤프 ORM·importer·admin·browse |

페르소나: [`persona/denny.md`](../../../persona/denny.md). 경로 glob 규칙: [`.cursor/rules/django-apps.mdc`](../../../.cursor/rules/django-apps.mdc).

### `game_data` 레이아웃

| 경로 | 책임 |
|------|------|
| `models/` | 구체 필드·FK/OneToOne·`Meta.constraints` (도메인 모델) |
| `importers/` | JSON → ORM 결정적 import |
| `services/` | 분류·검증·`validators.assert_no_domain_json_fields` |
| `browse/` | taxonomy → admin 대시보드 (thin view) |
| `admin.py` | aggregate root `ModelAdmin`·inlines |
| `management/commands/import_game_data.py` | CLI import + post-import guards |

Browse URL: `config/urls.py` → `path("admin/game-data/", include("django_apps.game_data.browse.urls"))`.

## domain JSON 금지 (`game_data`)

- 도메인 모델에 **`JSONField` 금지** (스키마 없는 덤프 방지).
- 필드명 `raw_json`, `payload`, `data`, `source_dump`, `audit_blob` **금지**.
- 예외: `ALLOWED_JSON_MODELS`에 모델명을 명시하고 **플랜·ADR 승인** 후에만 ([`validators.py`](../../../django_apps/game_data/services/validators.py), [`test_no_raw_json_domain_storage.py`](../../../tests/unit/game_data/test_no_raw_json_domain_storage.py)).
- `audit_blob` 등 레거시는 **마이그레이션으로 concrete 테이블**로 이전; 런타임 모델에 남기지 않는다.

## 블루프린트 격자 좌표 (공통)

블루프린트 복사 격자는 **`X == 0`인 열이 없다**(`1`과 `-1`이 동서로 인접; `0` 비경유). 서버 코드 `(x, y)`에서도 **`x == 0` 불가**. 상세·근거: [`research_blueprint_grid_coordinates_2026-05-10.md`](../../research/research_blueprint_grid_coordinates_2026-05-10.md).

## 의존 방향 (금지 위반 금지)

- `shapez_core` → `web`, `shapez_solver`, `asteroid_lab` **import 금지**
- `shapez_solver` → `shapez_core` 만 허용 · `web`·`asteroid_lab` import **금지**
- `asteroid_lab` → `shapez_core` 만 허용(향후)·스켈레톤에서는 미사용 가능 · `web`·`shapez_solver` import **금지**
- `web` → `shapez_core`, `shapez_solver`, `asteroid_lab`, `game_data` 허용
- `game_data` → `web`, `shapez_solver`, `asteroid_lab` **import 금지** (`shapez_core`만 허용, 향후)
- `shapez_core`·`shapez_solver`·`asteroid_lab` → `game_data` **import 금지**

기계 검증: [`tests/unit/architecture/test_django_app_import_boundaries.py`](../../../tests/unit/architecture/test_django_app_import_boundaries.py).

정본: [`.cursor/rules/architecture.mdc`](../../../.cursor/rules/architecture.mdc).

## 뷰·엔드포인트

- HTTP 엔드포인트는 **동작을 소유한 앱**에 둔다.
- 뷰는 얇게: 도메인·솔버 규칙은 `services/`·`importers/`·use case로 ([데니](../../../persona/denny.md) · 아래 참조 Rule 1).

## 참조 (외부 — Django 작업 시)

이 레포 정본은 [`.cursor/rules/django-apps.mdc`](../../../.cursor/rules/django-apps.mdc) + 본 매뉴얼이다. 아래는 **보조 참고**이며, 충돌 시 레포 규칙·import 행렬·`game_data` JSON 금지가 우선한다.

| 주제 | 링크 | 이 레포에서의 쓰임 |
|------|------|-------------------|
| Cursor modular rules · thin views · query/migration/testing 습관 | [Cursor Rules for Django (DEV)](https://dev.to/olivia_craft/cursor-rules-for-django-the-complete-guide-to-ai-assisted-django-development-3je5) | `.cursor/rules/*.mdc` 분리 방식과 동일; 뷰 30줄 smell·`select_related`·서비스 레이어는 데니 체크리스트와 정합 |
| 객체 단위 권한 · predicate · `ObjectPermissionBackend` | [django-rules — Using rules with Django](https://github.com/dfunckt/django-rules#using-rules-with-django) | **신규** staff/API object permission 도입 시: `rules` 앱·backend 설정·`rules.add_perm` / `Model` `Meta.rules_permissions` 패턴을 이 문서 기준으로 맞춘다. 현재 레포는 django-allauth + `LoginRequiredMixin` / `@staff_member_required` 위주 |

**DEV 가이드 ↔ 레포 매핑 (요약)**

- Rule 1 (fat models / thin views) → [django-apps.mdc](../../../.cursor/rules/django-apps.mdc) Thin view 절
- Rule 2 (query discipline) → list/admin/browse queryset에 `select_related` / `prefetch_related` 검토
- Rule 3–4 (migrations, settings) → [`database.md`](database.md), [`environment.md`](environment.md)
- Rule 5 (testing) → [`testing.md`](testing.md), `tests/unit/<app>/`
- Modular rules → `django-apps.mdc` + [`asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc) (앱별 glob)

## 실행

```bash
python manage.py runserver
```

설치: 루트에서 `pip install -e ".[dev]"`.

환경 변수 분류·`.env` / `.env.debug` 계층: [`environment.md`](environment.md).

## 인증

`django-allauth`, `accounts/` URL. OAuth 클라이언트는 코드가 아니라 환경·`SocialApp` 등으로 등록.

## 다음에 읽을 것

- 모델·마이그레이션: [`database.md`](database.md)
- 솔버 로직: [`solver.md`](solver.md)
