import pytest
from allauth.account import app_settings as account_app_settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


def test_signup_fields_include_email_for_social_signup_form() -> None:
    """allauth socialaccount SignupForm always passes email_required into BaseSignupForm."""
    assert "email" in account_app_settings.SIGNUP_FIELDS


def test_social_email_authentication_enabled_for_existing_local_users() -> None:
    """Provider-verified email can log into a matching local account (see social_adapter)."""
    from allauth.socialaccount import app_settings as social_app_settings

    assert social_app_settings.EMAIL_AUTHENTICATION is True
    assert social_app_settings.EMAIL_AUTHENTICATION_AUTO_CONNECT is True


@pytest.mark.django_db
def test_signup_page_renders_password_and_social_options() -> None:
    response = Client().get(reverse("account_signup"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Sign up" in content
    assert "Create account" in content
    assert "Social sign up" in content
    assert "Google" in content


@pytest.mark.django_db
def test_login_page_renders_password_and_social_options() -> None:
    response = Client().get(reverse("account_login"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Login" in content
    assert "Social login" in content
    assert "Google" in content


@pytest.mark.django_db
def test_signup_creates_user_and_redirects_home() -> None:
    response = Client().post(
        reverse("account_signup"),
        data={
            "username": "factory_user",
            "password1": "complex-password-123",
            "password2": "complex-password-123",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == "/"
    assert get_user_model().objects.filter(username="factory_user").exists()


@pytest.mark.django_db
def test_login_accepts_created_user() -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="solver_user", password="complex-password-123")

    response = Client().post(
        reverse("account_login"),
        data={
            "login": "solver_user",
            "password": "complex-password-123",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == "/"


@pytest.mark.django_db
def test_logout_clears_session() -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="logout_user", password="complex-password-123")
    client = Client()
    assert client.login(username="logout_user", password="complex-password-123")

    response = client.post(reverse("account_logout"))

    assert response.status_code == 302
    assert response["Location"] == "/"
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_nav_shows_auth_links_for_anonymous_user() -> None:
    response = Client().get(reverse("web:home"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'href="/accounts/login/"' in content
    assert 'href="/accounts/signup/"' in content


@pytest.mark.django_db
def test_nav_shows_user_and_logout_for_authenticated_user() -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="nav_user", password="complex-password-123")
    client = Client()
    assert client.login(username="nav_user", password="complex-password-123")

    response = client.get(reverse("web:home"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "nav_user" in content
    assert 'action="/accounts/logout/"' in content
