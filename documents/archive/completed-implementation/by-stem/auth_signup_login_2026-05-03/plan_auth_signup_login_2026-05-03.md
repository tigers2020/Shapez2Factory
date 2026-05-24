# Sign-up and login feature plan (2026-05-03)

## Goals

Add standard sign-up, login, logout, and basic social sign-up/login flows to the web app using `django-allauth`. Limit changes to configuration and the `web` interface layer without a custom user model or domain layer changes.

## Change targets

- `config/settings.py`
  - Add `django-allauth` apps, auth backends, `SITE_ID`, login/logout redirect settings
  - Add Google/GitHub provider apps
- `pyproject.toml`
  - Add `django-allauth` dependency
- `config/urls.py`
  - Mount `allauth.urls` under `accounts/`
- `django_apps/web/urls.py`
  - Redirect `sign-up`, `log-in`, `log-out` aliases from existing namespace to allauth URLs if needed
- `django_apps/web/templates/account/login.html`
  - Login template with standard form and social login buttons
- `django_apps/web/templates/account/signup.html`
  - Sign-up template with standard form and social sign-up buttons
- `django_apps/web/templates/account/logout.html`
  - Logout confirmation template
- `django_apps/web/templates/web/partials/site_nav.html`
  - Show login/sign-up or username/logout based on auth state
- `tests/integration/web/test_auth.py`
  - Tests for sign-up, login, logout, navigation, social button rendering

## Implementation method

1. Add `django-allauth` dependency and configure `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`, `allauth.socialaccount.providers.github`.
2. Configure `django.contrib.sites` and `allauth.account.middleware.AccountMiddleware`.
3. Set `AUTHENTICATION_BACKENDS` to Django default plus allauth backend.
4. Add `path("accounts/", include("allauth.urls"))` to `config/urls.py`.
5. Navigation login/sign-up links use allauth URL names `account_login`, `account_signup`, `account_logout`.
6. Login/sign-up templates expose Google/GitHub via `github_login`, `google_login` URL names so rendering does not fail before `SocialApp` registration.
7. Do not embed OAuth secrets in code; connect via admin `SocialApp` or environment configuration.

## Decisions to confirm before approval

- TODO: follow allauth default post–sign-up login policy.
- TODO: do not require email field in this scope.
- TODO: include Google/GitHub as default social providers; human registers client ID and secret in production.
- TODO: page-level auth requirements out of scope; this request is sign-up/login only.

## Verification

- `pytest tests/integration/web/test_auth.py`
- `pytest`
- `ruff check .`
- `mypy .`
- `black --check .`

## Migration

Do not create new migrations for project apps. Apply external app migrations from `django-allauth` and `django.contrib.sites` via `python manage.py migrate`.
