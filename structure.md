# shapez2Solver — 저장소 구조

이 문서는 **현재 워크스페이스 기준** 디렉터리·패키지·Django 앱·검증 설정을 요약한다. 상세 워크플로·역할 분담은 [AGENTS.md](AGENTS.md), 아키텍처 규칙은 [.cursor/rules/architecture.mdc](.cursor/rules/architecture.mdc)를 본다.

---

## 한 줄 요약

- **Python 패키지** `shapez2_solver` (`src/`) — shapez 2 솔버·플래너 도메인/애플리케이션 코드(스캐폴드 단계).
- **Django 5.x** (`config/`, `django_apps/`) — 공장 플래너용 웹/API 스캐폴드, SQLite, 정적·템플릿 UI.
- **프론트 빌드** — Tailwind CSS v4 CLI로 `assets/css/input.css` → `django_apps/web/static/web/css/app.css`.

---

## 루트 디렉터리 맵

| 경로 | 역할 |
|------|------|
| [src/shapez2_solver/](src/shapez2_solver/) | setuptools `where = ["src"]` 기준 설치 패키지 |
| [config/](config/) | Django 프로젝트 설정(`settings`, `urls`, `wsgi`/`asgi`) |
| [django_apps/](django_apps/) | 프로젝트 전용 Django 앱 (`projects`, `web`, `api`) |
| [tests/](tests/) | `pytest` + `pytest-django` (`pytest.ini`에서 `DJANGO_SETTINGS_MODULE`) |
| [documents/](documents/) | 리서치·플랜·메모·개발 계획 MD |
| [protocols/](protocols/) | 다단계 개발 파이프라인 정본 ([protocols/README.md](protocols/README.md)) |
| [persona/](persona/) | 페르소나 카드(역할·레이어 매핑) |
| [.cursor/](.cursor/) | Cursor 규칙·MCP 설정 |
| [assets/css/](assets/css/) | Tailwind 입력 CSS (`input.css`) |
| [manage.py](manage.py) | Django 관리 스크립트 |
| [pyproject.toml](pyproject.toml) | 패키지 메타, 의존성, black/ruff/mypy |
| [pytest.ini](pytest.ini) | pytest-django 설정 |
| [package.json](package.json) | CSS 빌드/워치 npm 스크립트 |

생성물·도구 캐시(일반적으로 버전 관리 제외): `node_modules/`, `.pytest_cache/`, `db.sqlite3` 등 — [.gitignore](.gitignore) 참고.

---

## `src/shapez2_solver/` (레이어드 코어)

목표 아키텍처(AGENTS 기준)는 `domain` → `application` → `adapters` → `interfaces` → `bootstrap` 이다. **현재 트리에 존재하는 것만** 아래에 적는다.

```text
src/shapez2_solver/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── shape.py          # 도형 코드 등 도메인 값
│   └── operation.py      # 도메인 연산/규칙 스텁
├── application/
│   ├── __init__.py
│   ├── planner_service.py
│   ├── solver_service.py # SolverRequest/Result, SolverService
│   └── ports/
│       └── __init__.py   # 포트(프로토콜) 확장 지점
└── infrastructure/
    └── __init__.py       # 인프라/어댑터 자리(현재 스캐폴드)
```

- **미배치 디렉터리**(문서·규칙상 예정): `adapters/`, `interfaces/`, `bootstrap/` — 필요 시 추가되며 이 파일을 갱신한다.

---

## `django_apps/` (웹·API·영속 모델)

```text
django_apps/
├── __init__.py
├── projects/
│   ├── apps.py
│   ├── admin.py
│   ├── models.py         # SolverProject, SolverRun 등
│   └── migrations/
├── web/
│   ├── apps.py
│   ├── urls.py
│   ├── views.py
│   ├── templates/web/    # base, home, gallery, demo, partials
│   └── static/web/       # app.css, JS (gallery-viewer 등)
└── api/
    ├── apps.py
    ├── urls.py
    └── views.py
```

- 루트 URL: [config/urls.py](config/urls.py) — `/admin/`, `/api/`, ``(web)``.

---

## `config/` (Django 프로젝트)

- [config/settings.py](config/settings.py): `INSTALLED_APPS`에 `django_apps.projects`, `django_apps.web`, `django_apps.api`; DB는 SQLite `db.sqlite3`.
- [config/urls.py](config/urls.py): 앱 URL include.

---

## `tests/`

| 파일 | 대략적 내용 |
|------|-------------|
| [tests/test_web_smoke.py](tests/test_web_smoke.py) | 홈/갤러리/데모 등 페이지 스모크 |
| [tests/test_api_health.py](tests/test_api_health.py) | API 헬스/기본 동작 |
| [tests/test_project_models.py](tests/test_project_models.py) | `projects` 모델 관련 |

---

## 문서·운영 규칙

| 경로 | 용도 |
|------|------|
| [documents/](documents/) | 게임 시스템 리서치, Django/갤러리/파이프라인 플랜, `CURSOR_MEMO`, 채팅 로그 등 |
| [AGENTS.md](AGENTS.md) | 에이전트·검증 파이프라인 요약 |
| [.cursor/rules/](.cursor/rules/) | root, architecture, persona-dialogue 등 |

---

## 자주 쓰는 명령

| 목적 | 명령 |
|------|------|
| 개발 의존성 설치 | `pip install -e ".[dev]"` |
| Django | `python manage.py runserver` / `migrate` 등 |
| 테스트 | `pytest` ([pytest.ini](pytest.ini) 기준 Django 설정 로드) |
| CSS 빌드 | `npm run build:css` ([package.json](package.json)) |
| 정적 검사(하네스) | `ruff check .` → `mypy src` → `black .` (CI는 `black --check .`) |

---

## 이 문서의 갱신 시점

- 새 Django 앱·새 `src/` 패키지 디렉터리·CI/배포 루트 추가 시 이 파일의 트리와 표를 맞춘다.

*생성 기준: 저장소 파일 스캔 및 `pyproject.toml` / `config/settings.py` 반영.*
