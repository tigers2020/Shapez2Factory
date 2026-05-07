"""Django settings for the shapez2 factory planner scaffold."""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = "django-insecure-scaffold-only-change-before-deploy"
DEBUG = True


def _split_hosts(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


# Render sets RENDER_EXTERNAL_HOSTNAME (e.g. app.onrender.com). Optional comma-separated
# DJANGO_ALLOWED_HOSTS for extra domains (custom hostnames on Render, local overrides).
_extra_hosts = _split_hosts(os.environ.get("DJANGO_ALLOWED_HOSTS", ""))
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS: list[str] = list(
    dict.fromkeys(_extra_hosts + ([_render_host] if _render_host else []))
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_apps.shapez_core.apps.ShapezCoreConfig",
    "django_apps.shapez_solver.apps.ShapezSolverConfig",
    "django_apps.web.apps.WebConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "django_apps" / "web" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_apps.web.context_processors.django_debug",
                "django_apps.web.context_processors.google_social_login_enabled",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_default_sqlite = (BASE_DIR / "db.sqlite3").resolve()
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{_default_sqlite.as_posix()}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("ko", "Korean"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# General user uploads (not shape part sprites; see SHAPE_PART_SPRITE_*).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Baked atomic part PNGs live under app static so they can be versioned like other assets.
SHAPE_PART_SPRITE_STATIC_ROOT = BASE_DIR / "django_apps" / "web" / "static" / "web"
SHAPE_PART_SPRITE_URL_PREFIX = "/static/web/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
# playwright_png: Node + Playwright (render_graph_preview.mjs). Often missing on PaaS runtime.
# noop: skip PNG graph thumbnails; Quick Solver 3D still uses /api/shape-preview/ in the browser.
# Macro graph tiles use preview_scene + sprite composition; warm PNG is optional — set noop on
# hosts without Node/Chromium to avoid timeouts (see graph_preview Playwright subprocess).
SOLVER_GRAPH_PREVIEW_RENDERER = (
    os.environ.get("SOLVER_GRAPH_PREVIEW_RENDERER", "playwright_png").strip().lower()
)
# filesystem: PNG files under SOLVER_GRAPH_PREVIEW_CACHE_DIR (ephemeral on many PaaS).
# database: store PNG bytes in web.GraphPreviewImage (Render Free friendly).
SOLVER_GRAPH_PREVIEW_STORAGE = (
    os.environ.get("SOLVER_GRAPH_PREVIEW_STORAGE", "filesystem").strip().lower()
)
SOLVER_GRAPH_PREVIEW_CACHE_DIR = BASE_DIR / ".graph_preview_cache"

# Public Ko-fi profile when SUPPORT_KOFI_URL is unset or blank (set to another URL to override).
SUPPORT_KOFI_URL = (
    os.environ.get("SUPPORT_KOFI_URL", "").strip() or "https://ko-fi.com/shapez2factory/"
)
SUPPORT_GITHUB_SPONSORS_URL = os.environ.get("SUPPORT_GITHUB_SPONSORS_URL", "").strip()
SUPPORT_PATREON_URL = os.environ.get("SUPPORT_PATREON_URL", "").strip()
# Support page crypto tabs; QR files: django_apps/web/static/web/images/support/{bch,eth}_qr.png
SUPPORT_BCH_ADDRESS = (
    os.environ.get("SUPPORT_BCH_ADDRESS", "").strip()
    or os.environ.get("SUPPORT_BITCOIN_ADDRESS", "").strip()
    or "1CYVnLMkGq9u8u1JDnH4aCFWXLTTZ6be2j"
)
SUPPORT_ETH_ADDRESS = (
    os.environ.get("SUPPORT_ETH_ADDRESS", "").strip()
    or "0xa921081Bf8B548987188f3a87e7728F047301CfE"
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = 1
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = {"username"}
# `email` must appear (optional `email` or required `email*`) so socialaccount's
# SignupForm can pass `email_required` into BaseSignupForm (allauth raises
# ImproperlyConfigured if the key is missing from SIGNUP_FIELDS).
ACCOUNT_SIGNUP_FIELDS = ["username*", "email", "password1*", "password2*"]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Request email from OAuth providers when available (still compatible with
# optional `email` in ACCOUNT_SIGNUP_FIELDS).
SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_FORMS = {
    "signup": "django_apps.web.socialaccount_forms.SocialSignupForm",
}

# If a trusted OAuth provider returns a verified email that already exists on a
# local user, log in that user and connect the social account (skip 3rdparty
# signup). Only safe with providers you trust — we use Google only for now.
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_ADAPTER = "django_apps.web.social_adapter.SocialAccountAdapter"

# Social login: either add a SocialApp in admin (linked to Site SITE_ID) or set
# OAuth env vars below. Without both client id and secret, /accounts/<provider>/login/
# raises SocialApp.DoesNotExist.
# Do not define the same provider twice (admin SocialApp + APP here): two apps
# for one provider can break login (wrong client_id/secret or MultipleObjectsReturned).
_social_providers: dict[str, dict] = {}
_google_cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
_google_sec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
if _google_cid and _google_sec:
    _social_providers["google"] = {
        "APP": {"client_id": _google_cid, "secret": _google_sec},
        # openid: Google returns id_token; profile/email: userinfo + django-allauth.
        "SCOPE": ["openid", "profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
SOCIALACCOUNT_PROVIDERS = _social_providers
