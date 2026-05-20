# 환경 변수 정책

로컬·배포에서 쓰는 환경 변수의 **분류·이름·기본값**을 한곳에 모은다. 구현 계약(CANON)은 아니다.

## 파일 계층

| 파일 | Git | 역할 |
|------|-----|------|
| `.env.example` | 추적 | secrets·DB 모드·OAuth 등 **최소 런타임** 템플릿 |
| `.env.debug.example` | 추적 | 관측·디버그·프리뷰 noop 등 **선택** 템플릿 |
| `.env` | 무시 | 개발자 로컬 (복사본) |
| `.env.debug` | 무시 | `.env` 위에 덮어쓰기 (`config/settings.py`에서 `override=True`) |

로드 순서: `.env` → `.env.debug`(있을 때만).

## 분류

| 클래스 | 설명 | 예 |
|--------|------|-----|
| **runtime** | 로컬/배포에 필요한 인프라·데이터 경로 | `DATABASE_URL`, `DJANGO_USE_SQLITE`, `SHAPEZ_BASEDATA_ROOT` |
| **feature** | 제품 동작 토글(코드에 reader 있음) | (현재 Asteroid Lab replay 전용 feature 토글 없음) |
| **infra** | 그래프 PNG 프리뷰·캐시 등 | `SOLVER_GRAPH_PREVIEW_*` |
| **debug** | 기본 `.env`에 두지 않음 | `ASTEROID_LAB_BOUNDARY_JSONL`, `SHAPEZ_COPY_DEBUG_DIR` |
| **unused** | `.env`에만 남은 이름 — **코드 미참조, 삭제** | `SHAPEZ_MINING_*`, `ASTEROID_LAB_REPLAY_JSON_DELIVERY` 등 |

## Boolean 표기

- **문서·예시 파일**: `0` / `1`만 사용한다.
- **파서**: 기존 호환을 위해 `true`, `yes`, `on`도 허용하는 모듈이 있다(`DJANGO_USE_SQLITE`, `ASTEROID_LAB_BOUNDARY_JSONL` 등). 신규 키는 `0`/`1` 우선.

## Reader 위치

| 키 | 기본값 | 읽는 모듈 |
|----|--------|-----------|
| `DJANGO_USE_SQLITE` | off | `config/settings.py` |
| `DATABASE_URL` | sqlite `db.sqlite3` | `config/settings.py` + dj_database_url |
| `SHAPEZ_BASEDATA_ROOT` | `documents/shapez_2_data/basedata-v1137` | `config/settings.py` |
| `SOLVER_GRAPH_PREVIEW_RENDERER` | `playwright_png` | `config/shapez_runtime_flags.py` |
| `SOLVER_GRAPH_PREVIEW_STORAGE` | `filesystem` | `config/shapez_runtime_flags.py` |
| `SOLVER_GRAPH_PREVIEW_CACHE_DIR` | `<BASE_DIR>/.graph_preview_cache` | `config/shapez_runtime_flags.py` |
| `ASTEROID_LAB_RUNTIME_GENE_TEMPLATES_PATH` | `tests/fixtures/asteroid_lab/gene_templates` | `config/settings.py` |
| `ASTEROID_LAB_BOUNDARY_JSONL` | off | `django_apps/asteroid_lab/observability/boundary_jsonl.py` |
| `ASTEROID_LAB_BOUNDARY_JSONL_DIR` | `var/asteroid_boundary_logs` | 동일 |
| `SHAPEZ_COPY_DEBUG_DIR` | off (빈 문자열) | `config/shapez_runtime_flags.py` (소비 코드 없음 — 덤프 경로 예약) |

OAuth·Support URL 등은 `config/settings.py`를 본다.

## 금지·주의

1. **Phantom flag**: 코드에 `os.environ.get`이 없는 이름을 `.env` / `.env.example`에 넣지 않는다.
2. **구현 전 env**: Sequence 13C lazy replay 등 **승인·구현 전**에는 `ASTEROID_LAB_REPLAY_*` 같은 이름을 미리 두지 않는다. 구현 시 이 문서와 `settings` 한 곳에 canonical 이름을 등록한다.
3. **Alias 중복**: `ENABLE_*` / `LAB_*` 두 이름으로 같은 기능을 켜지 않는다. reader가 없으면 문서에도 “env 없음”으로 표기한다.
4. **솔버 pass 플래그**: `SHAPEZ_MINING_PASS*` 등은 현재 코드베이스에 reader가 없다. 레거시 `.env` 항목은 제거한다.
5. **비밀값**: `.env`만. Markdown·커밋에 credentials 넣지 않는다.

## 미구현 기능과 문서

- **11B optimization overlay**: env 플래그 없음. 구현 시 별도 설계·이 문서 갱신.
- **13C lazy Lab replay**: env·settings는 **사람 승인 후 구현 단계**에서만 추가. [`asteroid_lab_13_replay_payload_scalability.md`](../../Algorithm/asteroid_lab_13_replay_payload_scalability.md) 참고.

## 관련 매뉴얼

- Django 실행: [`django.md`](django.md)
- Cloud VM·프리뷰 noop: [`cursor_usage.md`](cursor_usage.md)
- 테스트 게이트: [`testing.md`](testing.md)
