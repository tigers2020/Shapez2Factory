# 회원가입 및 로그인 기능 조사 (2026-05-03)

## 요청 요약

- 사용자는 회원가입 및 로그인 기능 추가를 요청했다.
- 추가 요청으로 기본 소셜 회원가입 및 로그인도 포함해야 한다.
- 현재 프로젝트 규칙상 구현 전 `documents/`에 조사 문서와 플랜 문서를 남기고, 사람이 플랜을 승인한 뒤 코드 수정으로 넘어가야 한다.

## 현재 구조

- `config/settings.py`에는 이미 `django.contrib.auth`, `django.contrib.sessions`, `django.contrib.messages`가 등록되어 있다.
- `AuthenticationMiddleware`, `SessionMiddleware`, `CsrfViewMiddleware`, `MessageMiddleware`도 이미 활성화되어 있다.
- 템플릿 컨텍스트 프로세서에 `request`, `auth`, `messages`가 포함되어 있어 네비게이션에서 로그인 상태를 바로 사용할 수 있다.
- 루트 URL은 `config/urls.py`에서 `django_apps.web.urls`를 `/`에 연결한다.
- 웹 앱은 현재 `django_apps/web/views.py`의 함수 기반 뷰와 `django_apps/web/templates/web/` 템플릿을 중심으로 구성되어 있다.
- 공통 네비게이션은 `django_apps/web/templates/web/partials/site_nav.html`에서 관리된다.

## 인증 기능 적용 지점

- 일반 회원가입, 로그인, 로그아웃과 소셜 인증을 함께 제공하려면 `django-allauth`를 쓰는 편이 가장 작다.
- `django-allauth` 공식 문서는 `allauth`, `allauth.account`, `allauth.socialaccount`, 제공자 앱을 `INSTALLED_APPS`에 추가하고 `path("accounts/", include("allauth.urls"))`를 연결하는 방식을 안내한다.
- OAuth 제공자는 대개 제공자 콘솔에서 API 클라이언트 또는 앱을 만들고, Django admin의 `SocialApp` 또는 `SOCIALACCOUNT_PROVIDERS` 설정으로 클라이언트 ID와 secret을 제공해야 한다.
- 기본 제공자로는 개발자가 토큰을 쉽게 만들 수 있는 GitHub와 일반 사용자 친화적인 Google을 우선 고려한다.
- 로그인 성공 후 이동 경로는 설정값 `LOGIN_REDIRECT_URL`로 관리하는 것이 Django 관례에 맞다.
- 로그아웃 후 이동 경로는 `LOGOUT_REDIRECT_URL`로 관리한다.

## 참고한 공식 문서

- `django-allauth` Quickstart: https://docs.allauth.org/en/dev/installation/quickstart.html
- `django-allauth` Providers: https://docs.allauth.org/en/dev/socialaccount/providers/index.html

## 테스트 관점

- 회원가입 페이지 GET 응답과 폼 렌더링을 확인한다.
- 유효한 일반 회원가입 POST가 사용자를 생성하고 홈으로 리다이렉트하는지 확인한다.
- 로그인 페이지 GET 응답과 유효한 로그인 POST 리다이렉트를 확인한다.
- 로그아웃 POST가 세션을 종료하는지 확인한다.
- 네비게이션에서 비로그인 상태는 로그인/회원가입 링크, 로그인 상태는 사용자명/로그아웃 액션을 노출하는지 확인한다.
- 소셜 로그인 링크가 설정된 제공자 기준으로 렌더링되는지 확인한다.

## 위험 및 제약

- 기본 `User` 모델을 계속 사용하면 사용자 모델 마이그레이션은 필요하지 않다.
- `django-allauth`를 추가하면 `account`, `socialaccount`, `sites` 관련 기본 마이그레이션 적용이 필요하다.
- 실제 OAuth 동작은 각 제공자의 클라이언트 ID와 secret이 없으면 완료할 수 없다.
- TODO: 회원가입 시 이메일 필수 여부는 아직 확정되지 않았다. allauth 기본 설정은 이메일 선택 입력으로 시작한다.
- TODO: 소셜 제공자는 Google과 GitHub를 기본 후보로 둔다. 운영 전에 실제 사용할 제공자를 사람이 확정해야 한다.
