# Sign-up and login feature research (2026-05-03)

## Request summary

- User requested sign-up and login functionality.
- Additional request: include basic social sign-up and login.
- Per project rules, leave research and plan documents under `documents/` before code changes, after human plan approval.

## Current structure

- `config/settings.py` already registers `django.contrib.auth`, `django.contrib.sessions`, `django.contrib.messages`.
- `AuthenticationMiddleware`, `SessionMiddleware`, `CsrfViewMiddleware`, `MessageMiddleware` are already enabled.
- Template context processors include `request`, `auth`, `messages` so navigation can use login state directly.
- Root URLs connect `django_apps.web.urls` at `/` via `config/urls.py`.
- Web app is function-based views in `django_apps/web/views.py` and templates under `django_apps/web/templates/web/`.
- Shared navigation is managed in `django_apps/web/templates/web/partials/site_nav.html`.

## Auth feature integration points

- `django-allauth` is the smallest change for standard sign-up/login/logout plus social auth together.
- Official docs add `allauth`, `allauth.account`, `allauth.socialaccount`, provider apps to `INSTALLED_APPS` and mount `path("accounts/", include("allauth.urls"))`.
- OAuth providers typically need API client/app from provider console and client ID/secret via Django admin `SocialApp` or `SOCIALACCOUNT_PROVIDERS`.
- Default providers: GitHub (easy dev tokens) and Google (user-friendly).
- Post-login redirect via `LOGIN_REDIRECT_URL` matches Django convention.
- Post-logout redirect via `LOGOUT_REDIRECT_URL`.

## Official documentation referenced

- `django-allauth` Quickstart: https://docs.allauth.org/en/dev/installation/quickstart.html
- `django-allauth` Providers: https://docs.allauth.org/en/dev/socialaccount/providers/index.html

## Testing perspective

- Verify sign-up page GET and form rendering.
- Verify valid sign-up POST creates user and redirects home.
- Verify login page GET and valid login POST redirect.
- Verify logout POST ends session.
- Verify navigation shows login/sign-up when logged out and username/logout when logged in.
- Verify social login links render for configured providers.

## Risks and constraints

- Continuing default `User` model avoids user model migration.
- Adding `django-allauth` requires applying default migrations for `account`, `socialaccount`, `sites`.
- OAuth cannot complete without provider client ID and secret.
- TODO: sign-up email requirement not decided; allauth defaults to optional email.
- TODO: Google and GitHub as default provider candidates; human must confirm providers before production.
