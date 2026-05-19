# 매뉴얼: Django · 백엔드

작업 전 [`AGENTS.md`](../../../AGENTS.md) Core Rules를 확인한다.

## 소유

| 앱 | 경로 | 책임 |
|----|------|------|
| shapez_core | `django_apps/shapez_core/` | 도형 규칙·파싱·정규화 |
| shapez_solver | `django_apps/shapez_solver/` | 솔버 유스케이스·서비스 |
| asteroid_lab | `django_apps/asteroid_lab/` | 소행성 실험실(ORM·디코드·리플레이; 레시피 솔버와 별도) |
| web | `django_apps/web/` | 템플릿·정적 자산·얇은 뷰 |

## 블루프린트 격자 좌표 (공통)

블루프린트 복사 격자는 **`X == 0`인 열이 없다**(`1`과 `-1`이 동서로 인접; `0` 비경유). 서버 코드 `(x, y)`에서도 **`x == 0` 불가**. 상세·근거: [`research_blueprint_grid_coordinates_2026-05-10.md`](../../research/research_blueprint_grid_coordinates_2026-05-10.md).

## 의존 방향 (금지 위반 금지)

- `shapez_core` → `web`, `shapez_solver`, `asteroid_lab` **import 금지**
- `shapez_solver` → `shapez_core` 만 허용 · `web`·`asteroid_lab` import **금지**
- `asteroid_lab` → `shapez_core` 만 허용(향후)·스켈레톤에서는 미사용 가능 · `web`·`shapez_solver` import **금지**
- `web` → `shapez_core`, `shapez_solver`, `asteroid_lab` 허용

정본: [`.cursor/rules/architecture.mdc`](../../../.cursor/rules/architecture.mdc).

## 뷰·엔드포인트

- HTTP 엔드포인트는 **동작을 소유한 앱**에 둔다.
- 뷰는 얇게: 도메인·솔버 규칙은 서비스/유스케이스로.

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
