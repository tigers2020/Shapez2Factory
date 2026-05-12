# 회원가입 및 로그인 기능 플랜 (2026-05-03)

## 목표

`django-allauth`를 사용해 웹 앱에 일반 회원가입, 로그인, 로그아웃, 기본 소셜 회원가입·로그인 흐름을 추가한다. 별도 사용자 모델이나 도메인 레이어 변경 없이 설정과 `web` 인터페이스 레이어 변경으로 제한한다.

## 변경 대상

- `config/settings.py`
  - `django-allauth` 앱, 인증 백엔드, `SITE_ID`, 로그인/로그아웃 리다이렉트 설정 추가
  - Google/GitHub 제공자 앱 추가
- `pyproject.toml`
  - `django-allauth` 의존성 추가
- `config/urls.py`
  - `accounts/`에 `allauth.urls` 연결
- `django_apps/web/urls.py`
  - 필요 시 기존 네임스페이스에서 `sign-up`, `log-in`, `log-out` 별칭을 allauth URL로 리다이렉트
- `django_apps/web/templates/account/login.html`
  - 일반 로그인 폼과 소셜 로그인 버튼을 포함한 템플릿 추가
- `django_apps/web/templates/account/signup.html`
  - 일반 회원가입 폼과 소셜 회원가입 버튼을 포함한 템플릿 추가
- `django_apps/web/templates/account/logout.html`
  - 로그아웃 확인 템플릿 추가
- `django_apps/web/templates/web/partials/site_nav.html`
  - 로그인 상태에 따라 로그인/회원가입 또는 사용자명/로그아웃 표시
- `tests/integration/web/test_auth.py`
  - 일반 회원가입, 로그인, 로그아웃, 네비게이션, 소셜 버튼 렌더링 테스트 추가

## 구현 방식

1. `django-allauth`를 의존성에 추가하고 `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`, `allauth.socialaccount.providers.github`를 설정한다.
2. `django.contrib.sites`와 `allauth.account.middleware.AccountMiddleware`를 설정한다.
3. `AUTHENTICATION_BACKENDS`에 Django 기본 백엔드와 allauth 백엔드를 함께 둔다.
4. `config/urls.py`에 `path("accounts/", include("allauth.urls"))`를 추가한다.
5. 네비게이션의 로그인/회원가입 링크는 allauth URL 이름인 `account_login`, `account_signup`, `account_logout`을 사용한다.
6. 로그인·회원가입 템플릿은 `github_login`, `google_login` URL 이름을 사용해 Google/GitHub 소셜 로그인 링크를 노출한다. `SocialApp` 등록 전에도 화면 렌더링이 실패하지 않게 하기 위함이다.
7. 실제 OAuth secret은 코드에 넣지 않고 admin `SocialApp` 등록 또는 환경 설정으로 연결한다.

## 승인 전 확인할 결정

- TODO: 일반 회원가입 후 allauth 기본 흐름에 따른 로그인 정책을 따른다.
- TODO: 이메일 필드는 이번 범위에서 필수화하지 않는다.
- TODO: Google/GitHub를 기본 소셜 제공자로 포함하되, 실제 클라이언트 ID와 secret은 사람이 운영 환경에서 등록한다.
- TODO: 인증이 필요한 페이지 제한은 이번 범위에 포함하지 않는다. 현재 요청은 가입/로그인 기능 추가로 한정한다.

## 검증

- `pytest tests/integration/web/test_auth.py`
- `pytest`
- `ruff check .`
- `mypy .`
- `black --check .`

## 마이그레이션

프로젝트 앱의 새 마이그레이션 파일은 만들지 않는다. 다만 `django-allauth`와 `django.contrib.sites`가 제공하는 외부 앱 마이그레이션은 `python manage.py migrate`로 적용해야 한다.
